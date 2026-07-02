from __future__ import annotations

import json
import operator
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from loguru import logger
from pydantic import BaseModel, Field
from uuid6 import uuid7

from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.adapters.qwen_cloud.chat_model import get_chat_model
from src.adapters.qwen_cloud.templates import render_prompt
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

_DEBATER_ROLES = (AgentRole.ADVOCATE, AgentRole.AUDITOR, AgentRole.ASSESSOR)
_RECEIPT_RE = re.compile(r'\[RECEIPT:\s*"([^"]+)"\s*,\s*"([^"]+)"\]')
_REF_RE = re.compile(r"\[REF:\s*(\d+)\]")

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


class _DebateState(TypedDict):
    turns: Annotated[list[DebateTurn], operator.add]
    round: int
    decision: Decision | None


def _is_pass(content: str) -> bool:
    return content.strip().rstrip(".").upper() == "PASS"


def _parse_receipts(content: str) -> list[Receipt]:
    return [
        Receipt(source_title=title, chunk_text=excerpt)
        for title, excerpt in _RECEIPT_RE.findall(content)
    ]


def _parse_references(content: str, transcript_len: int) -> list[int]:
    refs = {int(n) for n in _REF_RE.findall(content)}
    return sorted(n for n in refs if 0 <= n < transcript_len)


class LangGraphNegotiationEngine(NegotiationEngine):
    """LangGraph implementation of the simultaneous multi-round debate.

    Per round, the three debaters run in one parallel superstep over a shared
    append-only transcript (reducer state); each may PASS. The loop exits at
    the round cap or when a whole round passes, then the Arbitrator judges the
    transcript once and drafts the reply.
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

        # Hybrid grounding: one baseline retrieval shared by Advocate/Auditor;
        # agents can still dig further via the retrieval tool mid-turn.
        baseline_chunks = await self._baseline_chunks(outreach)
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
        }

        graph = self._build_graph(retrieval_tool, base_context, settings.DEBATE_MAX_TOOL_ROUNDS)
        final_state: _DebateState = await graph.ainvoke(
            {"turns": [], "round": 1, "decision": None}
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
        async def _debater(role: AgentRole, state: _DebateState) -> dict:
            turn = await self._debater_turn(
                role, state, retrieval_tool, base_context, max_tool_rounds
            )
            return {"turns": [turn]} if turn else {"turns": []}

        async def advocate(state: _DebateState) -> dict:
            return await _debater(AgentRole.ADVOCATE, state)

        async def auditor(state: _DebateState) -> dict:
            return await _debater(AgentRole.AUDITOR, state)

        async def assessor(state: _DebateState) -> dict:
            return await _debater(AgentRole.ASSESSOR, state)

        def gate(state: _DebateState) -> dict:
            return {}

        def route(state: _DebateState) -> str:
            spoke_this_round = any(t.round == state["round"] for t in state["turns"])
            if state["round"] >= self.round_cap or not spoke_this_round:
                return "arbitrator"
            return "advance"

        def advance(state: _DebateState) -> dict:
            return {"round": state["round"] + 1}

        async def arbitrator(state: _DebateState) -> dict:
            return await self._arbitrate(state, base_context)

        builder = StateGraph(_DebateState)
        builder.add_node("advocate", advocate)
        builder.add_node("auditor", auditor)
        builder.add_node("assessor", assessor)
        builder.add_node("gate", gate)
        builder.add_node("advance", advance)
        builder.add_node("arbitrator", arbitrator)

        for role in ("advocate", "auditor", "assessor"):
            builder.add_edge(START, role)
            builder.add_edge(role, "gate")
            builder.add_edge("advance", role)
        builder.add_conditional_edges(
            "gate", route, {"advance": "advance", "arbitrator": "arbitrator"}
        )
        builder.add_edge("arbitrator", END)
        return builder.compile()

    async def _debater_turn(
        self,
        role: AgentRole,
        state: _DebateState,
        retrieval_tool: BaseTool,
        base_context: dict[str, Any],
        max_tool_rounds: int,
    ) -> DebateTurn | None:
        transcript = state["turns"]
        prompt = render_prompt(
            f"{role.value}.j2",
            round_number=state["round"],
            prior_turns=transcript,
            **base_context,
        )
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
            return None

        return DebateTurn(
            round=state["round"],
            role=role,
            content=content,
            receipts=_parse_receipts(content) + tool_receipts,
            actions=actions,
            references_turn_ids=_parse_references(content, len(transcript)),
            created_at=datetime.now(UTC),
        )

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

    async def _arbitrate(self, state: _DebateState, base_context: dict[str, Any]) -> dict:
        prompt = render_prompt(
            "arbitrator.j2",
            prior_turns=state["turns"],
            round_cap=self.round_cap,
            custom_instructions=base_context.get("custom_instructions"),
        )
        model = self._chat_model_factory(AgentRole.ARBITRATOR).with_structured_output(
            ArbitratorRuling
        )
        result = await model.ainvoke(prompt)
        ruling = (
            result if isinstance(result, ArbitratorRuling) else ArbitratorRuling(**dict(result))
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
