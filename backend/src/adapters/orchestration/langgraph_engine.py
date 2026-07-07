from __future__ import annotations

import json
import operator
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from loguru import logger
from pydantic import BaseModel, Field, ValidationError
from uuid6 import uuid7

from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.adapters.qwen_cloud.chat_model import get_chat_model
from src.adapters.qwen_cloud.personas import (
    DEBATER_PERSONAS,
    first_name,
    persona_for,
)
from src.adapters.qwen_cloud.templates import render_prompt
from src.adapters.qwen_cloud.token_logging import reset_token_totals, token_totals
from src.adapters.qwen_cloud.tool_registry import tools_for_role
from src.config import get_settings
from src.domain.collaboration.negotiation_engine import DebateOutcome, NegotiationEngine
from src.domain.exceptions.base import DebateError
from src.domain.models.outreach import Decision, DecisionLabel, Outreach
from src.domain.models.professor import Professor
from src.domain.models.society import (
    ActionKind,
    AgentAction,
    AgentRole,
    DebateTrace,
    DebateTurn,
    Receipt,
)

_DEBATER_ROLES: tuple[AgentRole, ...] = (
    AgentRole.ADVOCATE,
    AgentRole.AUDITOR,
    AgentRole.ASSESSOR,
)
_RECEIPT_RE = re.compile(r'\[RECEIPT:\s*"([^"]+)"\s*,\s*"([^"]+)"\]')
_REF_RE = re.compile(r"\[REF:\s*(\d+)\]")
_CONTINUES_RE = re.compile(r"\s*\[CONTINUES\]\s*$")

# Prepended to a debater's prompt when it's picking up its *own* unfinished turn
# (it ended the previous one with [CONTINUES]). Overrides the base prompt's
# "live conversation, address the others" framing so the model doesn't fabricate
# an interlocutor or address itself by name mid-continuation.
_CONTINUATION_DIRECTIVE = (
    "YOU ARE CONTINUING YOUR OWN PREVIOUS STATEMENT. This is not a new turn and "
    "no one has spoken since you — pick up exactly where you left off, in the "
    "first person, and make your NEXT single point. Do NOT open by reacting to, "
    "quoting, agreeing with, or naming another debater, and never address "
    "yourself by name — you are still mid-thought. Any [REF:n] must point at a "
    "turn that already exists in the transcript below. End with [CONTINUES] "
    "again only if you still have a further, distinct point after this one.\n\n"
)

# How each bindable tool is classified on the replay's AgentAction chips.
_ACTION_KINDS: dict[str, tuple[ActionKind, str]] = {
    "retrieve_from_professor_corpus": (ActionKind.RETRIEVAL, "pgvector"),
    "claim_verification_tool": (ActionKind.SKILL, "claim-verification"),
    "capacity_math_tool": (ActionKind.SKILL, "capacity-math"),
    "mobility_lookup_tool": (ActionKind.MCP, "local-mcp-bus"),
}


class ArbitratorRuling(BaseModel):
    label: DecisionLabel
    rationale: str = Field(description="A few sentences grounded in the transcript.")
    drafted_reply: str = Field(description="A short, professional email reply to the candidate.")


class _ModeratorChoice(BaseModel):
    """The facilitator's routing decision for the next turn (MAD-style judge)."""

    next_speaker: Literal["advocate", "auditor", "assessor", "end"]
    reason: str = Field(description="One short clause on why, for the trace.")


class _DebateState(TypedDict):
    turns: Annotated[list[DebateTurn], operator.add]
    dispatched: Annotated[list[str], operator.add]
    round: int
    spoken_this_round: list[str]
    next_speaker: str
    # Set when the last turn ended with [CONTINUES]: the same debater still has
    # more to say, so the Moderator must route back to them next rather than
    # picking freely — this is what lets one point-per-turn stay speech-length
    # instead of one long turn covering every point at once.
    continuing_speaker: str | None
    # How many consecutive turns continuing_speaker has already taken — bounds
    # a single debater's streak regardless of how many times it says CONTINUES.
    continuation_count: int
    consecutive_passes: int
    turn_count: int
    decision: Decision | None


def _is_pass(content: str) -> bool:
    return content.strip().rstrip(".").upper() == "PASS"


def _split_continuation(content: str) -> tuple[str, bool]:
    """Strip a trailing [CONTINUES] marker, returning (clean_content, continues).

    A debater appends this when it has more distinct points queued up (e.g. the
    Auditor mid-way through a claim-by-claim audit) so the turn stays short and
    speech-length instead of one long wall covering every point at once."""
    match = _CONTINUES_RE.search(content)
    if not match:
        return content, False
    return content[: match.start()].rstrip(), True


def _log_turn(
    role: AgentRole,
    round_number: int,
    turn: DebateTurn | None,
    passed: bool,
    continues: bool,
    capped: bool,
    streak: int,
) -> None:
    """One human-readable line per debate turn: who spoke, a preview of what
    they said, any tools they reached for, and whether they yielded or hold the
    floor. This is the narrative that makes a background debate legible live."""
    name = persona_for(role).name
    if passed or turn is None:
        logger.info("💬 [R{}] {} ({}) passed", round_number, role.value.upper(), name)
        return

    preview = " ".join(turn.content.split())[:140]
    tool_note = ""
    if turn.actions:
        kinds = ", ".join(a.name for a in turn.actions)
        tool_note = f" · 🔧 {kinds}"
    tail = ""
    if capped:
        tail = " · ✋ continuation cap hit, yielding"
    elif continues:
        tail = f" · ↻ continues ({streak})"
    logger.info(
        '💬 [R{}] {} ({}){}: "{}"{}',
        round_number,
        role.value.upper(),
        name,
        tool_note,
        preview,
        tail,
    )


def _parse_receipts(content: str) -> list[Receipt]:
    return [
        Receipt(source_title=title, chunk_text=excerpt)
        for title, excerpt in _RECEIPT_RE.findall(content)
    ]


def _parse_references(content: str, transcript_len: int) -> list[int]:
    refs = {int(n) for n in _REF_RE.findall(content)}
    return sorted(n for n in refs if 0 <= n < transcript_len)


# How much of a receipt's quoted excerpt to keep when a turn is re-sent as prior
# context to a *later* turn. The full excerpt was needed the moment the receipt
# was made; on every subsequent turn's prompt it's dead weight that gets re-billed
# as input tokens, so we truncate it. The stored DebateTurn.content is untouched —
# only the transcript view fed into prompts is compacted.
_RECEIPT_EXCERPT_KEEP = 120


def _compact_receipt(match: re.Match[str]) -> str:
    title, excerpt = match.group(1), match.group(2)
    if len(excerpt) <= _RECEIPT_EXCERPT_KEEP:
        return match.group(0)
    return f'[RECEIPT: "{title}", "{excerpt[:_RECEIPT_EXCERPT_KEEP]}…"]'


def _compact_turns(turns: list[DebateTurn]) -> list[DebateTurn]:
    """A prompt-only view of the transcript with long receipt excerpts truncated.

    Returns lightweight copies (originals unchanged, so the persisted trace and
    the replay UI still carry the full receipts). This is the single biggest
    lever on the debate's quadratic token growth: verbose early turns stop being
    re-billed in full on every later prompt."""
    compacted: list[DebateTurn] = []
    for turn in turns:
        new_content = _RECEIPT_RE.sub(_compact_receipt, turn.content)
        if new_content == turn.content:
            compacted.append(turn)
        else:
            compacted.append(turn.model_copy(update={"content": new_content}))
    return compacted


def _first_unspoken(dispatched: set[str]) -> str:
    for role in _DEBATER_ROLES:
        if role.value not in dispatched:
            return role.value
    return _DEBATER_ROLES[0].value


class LangGraphNegotiationEngine(NegotiationEngine):
    """LangGraph implementation of the debate as a moderator-driven exchange
    (Liang et al. 2023, Multi-Agent Debate / MAD): debaters take sequential
    turns over one shared, append-only transcript — each sees everything said
    so far and rebuts it directly — while a lightweight Moderator (the cheap
    triage model acting as MAD's judge) routes the floor to whoever can best
    advance the argument and calls the debate when it stops being productive.

    This replaces the old simultaneous-talk scheme (ChatEval's least
    conversational strategy) where the three debaters spoke in parallel each
    round, blind to one another. Termination stays bounded: the Moderator can
    only end once every debater has held the floor at least once, and a hard
    turn cap (round_cap * debaters) backstops it regardless.
    """

    def __init__(
        self,
        round_cap: int,
        retriever: PublicationRetriever,
        chat_model_factory: Callable[[AgentRole | None], BaseChatModel] = get_chat_model,
    ) -> None:
        super().__init__(round_cap=round_cap)
        self._retriever = retriever
        self._chat_model_factory = chat_model_factory

    async def run(self, outreach: Outreach, professor: Professor) -> DebateOutcome:
        settings = get_settings()
        started_at = datetime.now(UTC)
        reset_token_totals()

        candidate = (
            outreach.extracted_profile.name
            if outreach.extracted_profile and outreach.extracted_profile.name
            else outreach.sender_name or outreach.sender_email
        )
        logger.info(
            "▶ Debate starting — candidate '{}' (round cap {})",
            candidate,
            self.round_cap,
        )

        # Hybrid grounding: one baseline retrieval shared by Advocate/Auditor;
        # agents can still dig further via the retrieval tool mid-turn.
        baseline_chunks = await self._baseline_chunks(outreach)
        logger.debug("  retrieved {} baseline corpus chunk(s)", len(baseline_chunks))
        retrieval_tool = self._retriever.as_tool()

        profile = outreach.extracted_profile.model_dump() if outreach.extracted_profile else {}
        base_context: dict[str, Any] = {
            "publication_chunks": baseline_chunks,
            "extracted_profile": profile,
            "extracted_claims": outreach.extracted_claims,
            "custom_instructions": professor.custom_instructions,
            "capacity": professor.capacity,
            "institution": professor.institution,
            "institution_country": professor.institution_country,
            # Persona layer — agents address each other and the professor by name.
            "cast": DEBATER_PERSONAS,
            "professor_first_name": first_name(professor.display_name),
        }

        # Seed the transcript with the Gatekeeper explaining why this outreach was
        # let through, so the debaters can build on (or push back against) it.
        opening = await self._gatekeeper_opening(outreach, base_context)

        graph = self._build_graph(retrieval_tool, base_context, settings.DEBATE_MAX_TOOL_ROUNDS)
        final_state: _DebateState = await graph.ainvoke(
            {
                "turns": [opening] if opening else [],
                "dispatched": [],
                "round": 1,
                "spoken_this_round": [],
                "next_speaker": "",
                "continuing_speaker": None,
                "continuation_count": 0,
                "consecutive_passes": 0,
                "turn_count": 0,
                "decision": None,
            }
        )

        decision = final_state["decision"]
        if decision is None:
            raise DebateError("Debate ended without an Arbitrator decision")

        trace = _build_trace(
            outreach=outreach,
            professor=professor,
            turns=final_state["turns"],
            round_cap=self.round_cap,
            started_at=started_at,
        )

        elapsed = (datetime.now(UTC) - started_at).total_seconds()
        totals = token_totals()
        debater_turns = sum(1 for t in trace.turns if t.role != AgentRole.ARBITRATOR)
        logger.info(
            "✔ Debate complete — {} · {} turns over {} round(s) · {:.1f}s · "
            "{} LLM calls, {} tok ({}+{})",
            decision.label.value.upper(),
            debater_turns,
            trace.terminated_at_round or 0,
            elapsed,
            totals["calls"],
            totals["input"] + totals["output"],
            totals["input"],
            totals["output"],
        )
        return DebateOutcome(trace=trace, decision=decision)

    async def _baseline_chunks(self, outreach: Outreach) -> list[dict]:
        profile = outreach.extracted_profile
        query_parts = list(profile.interests) if profile else []
        query_parts += [c.text for c in outreach.extracted_claims[:3]]
        query = "; ".join(query_parts) or outreach.subject or outreach.body[:200]
        try:
            results = await self._retriever.search(query)
        except Exception as exc:  # noqa: BLE001 — debate degrades to tool-only retrieval
            logger.warning("Baseline retrieval failed, continuing without: {}", exc)
            return []
        return [r.model_dump() for r in results[: get_settings().DEBATE_BASELINE_CHUNKS]]

    def _build_graph(
        self,
        retrieval_tool: BaseTool,
        base_context: dict[str, Any],
        max_tool_rounds: int,
    ):
        settings = get_settings()
        max_continuations = settings.DEBATE_MAX_CONTINUATIONS
        # A debater can now take multiple turns per round via [CONTINUES], so the
        # hard turn cap needs *some* headroom beyond "one turn per debater per
        # round" — but a modest multiplier, not the full continuation budget, or
        # the ceiling gets high enough for the debate to spiral before the
        # Moderator or all-passed check ever ends it.
        max_turns = (
            self.round_cap * len(_DEBATER_ROLES) * settings.DEBATE_TURN_CAP_MULTIPLIER
        )

        async def moderator(state: _DebateState) -> dict:
            return await self._moderate(state, base_context, max_turns)

        async def speak(state: _DebateState) -> dict:
            role = AgentRole(state["next_speaker"])
            transcript = state["turns"]
            is_continuation = state["continuing_speaker"] == role.value

            # Soft round grouping for the replay: a "round" is a wave in which
            # each role speaks at most once; looping back to a role starts a new
            # one. A continuation of the same still-unfinished point is not a
            # loop-back — it stays in the current round.
            round_number = state["round"]
            spoken_this_round = list(state["spoken_this_round"])
            if not is_continuation:
                if role.value in spoken_this_round:
                    round_number += 1
                    spoken_this_round = []
                spoken_this_round.append(role.value)

            turn, continues = await self._debater_turn(
                role,
                transcript,
                round_number,
                retrieval_tool,
                base_context,
                max_tool_rounds,
                is_continuation=is_continuation,
            )
            passed = turn is None
            # Force-stop a runaway continuer once the streak hits the cap,
            # regardless of what the model asked for — a hard safety net so a
            # single voice can never monopolize the debate turn after turn.
            next_count = state["continuation_count"] + 1 if is_continuation else 1
            capped = continues and next_count >= max_continuations
            continues = continues and next_count < max_continuations
            _log_turn(role, round_number, turn, passed, continues, capped, next_count)
            return {
                "turns": [] if passed else [turn],
                "dispatched": [role.value],
                "round": round_number,
                "spoken_this_round": spoken_this_round,
                "continuing_speaker": role.value if continues else None,
                "continuation_count": next_count if continues else 0,
                "consecutive_passes": 0 if continues else (
                    state["consecutive_passes"] + 1 if passed else 0
                ),
                "turn_count": state["turn_count"] + 1,
            }

        async def arbitrator(state: _DebateState) -> dict:
            return await self._arbitrate(state, base_context)

        def route(state: _DebateState) -> str:
            return "arbitrator" if state["next_speaker"] == "end" else "speak"

        builder = StateGraph(_DebateState)
        builder.add_node("moderator", moderator)
        builder.add_node("speak", speak)
        builder.add_node("arbitrator", arbitrator)
        builder.add_edge(START, "moderator")
        builder.add_conditional_edges(
            "moderator", route, {"speak": "speak", "arbitrator": "arbitrator"}
        )
        builder.add_edge("speak", "moderator")
        builder.add_edge("arbitrator", END)
        return builder.compile()

    async def _moderate(
        self, state: _DebateState, base_context: dict[str, Any], max_turns: int
    ) -> dict:
        """Pick who holds the floor next, or END. The floor only closes once
        every debater has spoken at least once; a hard turn cap and an
        all-passed check backstop the model so the debate always terminates."""
        dispatched = set(state["dispatched"])
        all_heard = {r.value for r in _DEBATER_ROLES} <= dispatched

        # A debater mid-way through a multi-point turn (ended with [CONTINUES])
        # always gets the floor back next — no need to ask the model, and no
        # other voice may interrupt a still-unfinished point.
        if state["continuing_speaker"] is not None:
            return {"next_speaker": state["continuing_speaker"]}

        # Hard safety nets — never let the model run the debate forever. Log
        # *which* backstop fired so a spiral vs. a clean close is legible.
        if state["turn_count"] >= max_turns:
            logger.info("🏁 Debate ending — hard turn cap ({} turns) reached", max_turns)
            return {"next_speaker": "end"}
        if all_heard and state["consecutive_passes"] >= len(_DEBATER_ROLES):
            logger.info("🏁 Debate ending — everyone passed; discussion resolved")
            return {"next_speaker": "end"}
        if not all_heard and state["consecutive_passes"] >= len(_DEBATER_ROLES):
            return {"next_speaker": _first_unspoken(dispatched)}

        prompt = render_prompt(
            "moderator.j2",
            prior_turns=_compact_turns(state["turns"]),
            dispatched=sorted(dispatched),
            all_heard=all_heard,
            **base_context,
        )
        model = self._chat_model_factory(AgentRole.GATEKEEPER).with_structured_output(
            _ModeratorChoice
        )
        try:
            result = await model.ainvoke(prompt)
            choice = (
                result
                if isinstance(result, _ModeratorChoice)
                else _ModeratorChoice(**dict(result))
            )
            pick: str = choice.next_speaker
        except Exception as exc:  # noqa: BLE001 — fall back to a safe rotation
            logger.warning("Moderator routing failed, falling back: {}", exc)
            pick = "end" if all_heard else _first_unspoken(dispatched)

        # The model may only end after every voice has been heard once.
        if pick == "end" and not all_heard:
            pick = _first_unspoken(dispatched)
        if pick == "end":
            logger.info("🏁 Debate ending — Moderator called it (discussion ran its course)")
        else:
            logger.debug("🎙 Moderator → {}", pick)
        return {"next_speaker": pick}

    async def _debater_turn(
        self,
        role: AgentRole,
        transcript: list[DebateTurn],
        round_number: int,
        retrieval_tool: BaseTool,
        base_context: dict[str, Any],
        max_tool_rounds: int,
        *,
        is_continuation: bool = False,
    ) -> tuple[DebateTurn | None, bool]:
        prompt = render_prompt(
            f"{role.value}.j2",
            round_number=round_number,
            prior_turns=_compact_turns(transcript),
            persona=persona_for(role),
            **base_context,
        )
        if is_continuation:
            # The model is being re-invoked to *continue its own* previous turn,
            # but the base prompt frames every call as "a live conversation —
            # answer challenges, name the person you're addressing." Without
            # this override it invents an interlocutor to react to (e.g. "Karen's
            # right…" before Karen has spoken) or addresses itself by name.
            prompt = _CONTINUATION_DIRECTIVE + prompt
        tools = tools_for_role(role, retrieval_tool)
        tools_by_name = {t.name: t for t in tools}
        model = self._chat_model_factory(role)
        bound = model.bind_tools(tools) if tools else model

        messages: list[BaseMessage] = [HumanMessage(content=prompt)]
        actions: list[AgentAction] = []
        tool_receipts: list[Receipt] = []

        response = await bound.ainvoke(messages)
        for _ in range(max_tool_rounds):
            if not isinstance(response, AIMessage) or not response.tool_calls:
                break
            messages.append(response)
            for tool_call in response.tool_calls:
                result = await self._invoke_tool(
                    tools_by_name, tool_call, actions, tool_receipts
                )
                messages.append(
                    ToolMessage(
                        content=json.dumps(result, default=str),
                        tool_call_id=tool_call["id"] or "",
                    )
                )
            response = await bound.ainvoke(messages)

        if isinstance(response, AIMessage) and response.tool_calls:
            # Tool budget exhausted mid-loop — force a plain text close-out.
            messages.append(response)
            messages.append(
                HumanMessage(content="Tool budget exhausted. Give your final turn now.")
            )
            response = await model.ainvoke(messages)

        content = str(response.content).strip()
        if not content or _is_pass(content):
            return None, False

        content, continues = _split_continuation(content)
        if not content:
            return None, False

        turn = DebateTurn(
            round=round_number,
            role=role,
            content=content,
            receipts=_parse_receipts(content) + tool_receipts,
            actions=actions,
            references_turn_ids=_parse_references(content, len(transcript)),
            created_at=datetime.now(UTC),
        )
        return turn, continues

    async def _invoke_tool(
        self,
        tools_by_name: dict[str, BaseTool],
        tool_call: ToolCall,
        actions: list[AgentAction],
        tool_receipts: list[Receipt],
    ) -> Any:
        name = tool_call["name"]
        args = tool_call.get("args") or {}
        kind, source = _ACTION_KINDS.get(name, (ActionKind.SKILL, None))
        tool = tools_by_name.get(name)
        if tool is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = await tool.ainvoke(args)
        except Exception as exc:  # noqa: BLE001 — a failed tool call shouldn't kill the round
            logger.warning("Debate tool {} failed: {}", name, exc)
            result = {"error": f"Tool failed: {exc}"}
        actions.append(
            AgentAction(
                kind=kind,
                name=name,
                detail=json.dumps(args, default=str)[:200],
                source=source,
            )
        )
        if name == "retrieve_from_professor_corpus" and isinstance(result, list):
            tool_receipts.extend(
                Receipt(
                    source_title=item.get("source_title", "Untitled publication"),
                    chunk_text=item.get("chunk_text", ""),
                )
                for item in result
                if isinstance(item, dict)
            )
        return result

    async def _gatekeeper_opening(
        self, outreach: Outreach, base_context: dict[str, Any]
    ) -> DebateTurn | None:
        """A short, in-character opening from the Gatekeeper on *why* this
        outreach earned a debate. Skipped (returns None) when triage recorded no
        reason (e.g. legacy rows); the debate then simply opens with the Advocate."""
        reason = outreach.triage_reason
        if not reason:
            return None
        prompt = render_prompt(
            "gatekeeper_opening.j2",
            triage_reason=reason,
            persona=persona_for(AgentRole.GATEKEEPER),
            **base_context,
        )
        model = self._chat_model_factory(AgentRole.GATEKEEPER)
        try:
            response = await model.ainvoke([HumanMessage(content=prompt)])
            content = str(response.content).strip()
        except Exception as exc:  # noqa: BLE001 — never let the opening block the debate
            logger.warning("Gatekeeper opening failed, using stored reason: {}", exc)
            content = ""
        if not content:
            content = reason
        logger.info(
            '💬 [R1] GATEKEEPER ({}) opens: "{}"',
            persona_for(AgentRole.GATEKEEPER).name,
            " ".join(content.split())[:140],
        )
        return DebateTurn(
            round=1,
            role=AgentRole.GATEKEEPER,
            content=content,
            created_at=datetime.now(UTC),
        )

    async def _arbitrate(self, state: _DebateState, base_context: dict[str, Any]) -> dict:
        capacity = base_context.get("capacity")
        prompt = render_prompt(
            "arbitrator.j2",
            prior_turns=state["turns"],
            round_cap=self.round_cap,
            persona=persona_for(AgentRole.ARBITRATOR),
            custom_instructions=base_context.get("custom_instructions"),
            cast=base_context.get("cast"),
            professor_first_name=base_context.get("professor_first_name"),
            # The Arbitrator scores the candidate against the professor's bar
            # directly — so it needs the raw profile/claims/topics, not just the
            # debaters' framing of them (guards against an unchallenged stretch).
            extracted_profile=base_context.get("extracted_profile"),
            extracted_claims=base_context.get("extracted_claims"),
            recruiting_topics=capacity.recruiting_topics if capacity else [],
        )
        logger.debug("⚖ Arbitrator ({}) deliberating…", persona_for(AgentRole.ARBITRATOR).name)
        raw_model = self._chat_model_factory(AgentRole.ARBITRATOR)
        structured = raw_model.with_structured_output(ArbitratorRuling)
        # Qwen's structured output is flaky on a long transcript: it either parses
        # to None, or emits an object missing a required field (which raises
        # ValidationError inside ainvoke). Weaker models drift to prose entirely.
        # Retry structured a few times, then fall back to plain JSON parsing — the
        # debate can't resolve without a ruling, so we exhaust both before giving up.
        ruling: ArbitratorRuling | None = None
        for attempt in range(get_settings().DEBATE_ARBITER_ATTEMPTS):
            ruling = await self._invoke_arbitrator(structured, prompt)
            if ruling is not None:
                break
            logger.warning("⚖ Arbitrator produced no usable ruling (attempt {})", attempt + 1)
        if ruling is None:
            logger.warning("⚖ Structured output exhausted — falling back to raw JSON")
            ruling = await self._arbitrate_json_fallback(raw_model, prompt)
        if ruling is None:
            raise DebateError("Arbitrator returned no structured ruling")
        logger.info(
            '⚖ Arbitrator rules {} — "{}"',
            ruling.label.value.upper(),
            " ".join(ruling.rationale.split())[:160],
        )
        closing_turn = DebateTurn(
            round=state["round"],
            role=AgentRole.ARBITRATOR,
            content=ruling.rationale,
            references_turn_ids=_parse_references(ruling.rationale, len(state["turns"])),
            created_at=datetime.now(UTC),
        )
        decision = Decision(
            label=ruling.label,
            rationale=ruling.rationale,
            drafted_reply=ruling.drafted_reply,
        )
        return {"turns": [closing_turn], "decision": decision}

    @staticmethod
    async def _invoke_arbitrator(model: Any, prompt: str) -> ArbitratorRuling | None:
        """One structured-output attempt, tolerant of Qwen's two flaky modes:
        a None parse, or an object missing `label` that raises ValidationError."""
        try:
            result = await model.ainvoke(prompt)
        except ValidationError as exc:
            logger.warning("⚖ Arbitrator ruling failed validation: {}", exc)
            return None
        if result is None:
            return None
        return (
            result if isinstance(result, ArbitratorRuling) else ArbitratorRuling(**dict(result))
        )

    @staticmethod
    async def _arbitrate_json_fallback(model: Any, prompt: str) -> ArbitratorRuling | None:
        """Last resort when `.with_structured_output` won't emit a valid object:
        ask the raw model for a plain JSON blob and parse it leniently. Weaker
        Qwen snapshots drift to prose under structured output but will produce
        clean JSON when asked directly — same tactic the single-agent baseline uses."""
        json_prompt = (
            prompt
            + '\n\nRespond with ONLY a JSON object, no prose, no code fence:\n'
            + '{"label": "invite|request_more_info|decline", "rationale": "...", '
            + '"drafted_reply": "..."}'
        )
        try:
            response = await model.ainvoke(json_prompt)
        except Exception as exc:  # noqa: BLE001 — fallback must never raise past here
            logger.warning("⚖ JSON-fallback call failed: {}", exc)
            return None
        text = str(response.content).strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            logger.warning("⚖ JSON-fallback produced no JSON object")
            return None
        try:
            data = json.loads(text[start : end + 1])
            return ArbitratorRuling(
                label=DecisionLabel(str(data["label"]).strip().lower()),
                rationale=str(data.get("rationale", "")),
                drafted_reply=str(data.get("drafted_reply", "")),
            )
        except (json.JSONDecodeError, KeyError, ValueError, ValidationError) as exc:
            logger.warning("⚖ JSON-fallback parse failed: {}", exc)
            return None


def _build_trace(
    *,
    outreach: Outreach,
    professor: Professor,
    turns: list[DebateTurn],
    round_cap: int,
    started_at: datetime,
) -> DebateTrace:
    debater_rounds = [t.round for t in turns if t.role != AgentRole.ARBITRATOR]
    return DebateTrace(
        id=uuid7(),
        outreach_id=outreach.id,
        professor_id=professor.id,
        turns=turns,
        round_cap=round_cap,
        terminated_at_round=max(debater_rounds) if debater_rounds else None,
        started_at=started_at,
        ended_at=datetime.now(UTC),
    )
