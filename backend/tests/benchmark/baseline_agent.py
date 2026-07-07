"""Single-agent baseline — the control the society is measured against.

One agent, one composite prompt that folds the whole job (assess research fit,
sanity-check the candidate's claims against the corpus, weigh capacity, decide).
It gets the *same* RAG tool over the *same* corpus and may loop tool calls, so
any quality gap is attributable to the society's structure (role division,
cross-examination, a separate arbitrator) and not to withheld tools or context.

It reasons step by step (chain-of-thought), verifies each claim, and weighs capacity
before deciding — the strongest single-agent control, so a society win means the
structure earned it. Token usage flows into the same `reset_token_totals()` /
`token_totals()` accumulator via TokenUsageCallback, so the runner attributes cost
per path.
"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_qwq import ChatQwen
from loguru import logger
from pydantic import SecretStr

from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.adapters.qwen_cloud.token_logging import TokenUsageCallback
from src.config import get_settings
from src.domain.models.outreach import Decision, DecisionLabel, Outreach
from src.domain.models.professor import Professor

# How many tool-call rounds and how much output the single agent is allowed. These
# are deliberately generous — the baseline is the STRONGEST single-agent control, so
# it must not be throttled by the debate's per-turn caps (DEBATE_MAX_TURN_TOKENS is
# tuned to keep a debater's turn short; a chain-of-thought verdict needs far more).
_BASELINE_TOOL_ROUNDS = 4
_BASELINE_MAX_TOKENS = 2000


def _baseline_model() -> ChatQwen:
    """The single-agent model, on the same Qwen model as the debaters (QWEN_MODEL_DEBATE)
    so any quality gap is structure, not model. Token usage flows into the shared
    accumulator via TokenUsageCallback, same as the debate path — but with a generous
    max_tokens so chain-of-thought reasoning isn't truncated (that would handicap the
    control we're trying to make strong)."""
    settings = get_settings()
    return ChatQwen(
        model=settings.QWEN_MODEL_DEBATE,
        base_url=settings.DASHSCOPE_BASE_URL,
        api_key=SecretStr(settings.DASHSCOPE_API_KEY),
        timeout=settings.DASHSCOPE_TIMEOUT,
        max_tokens=_BASELINE_MAX_TOKENS,
        enable_thinking=False,
        callbacks=[TokenUsageCallback("baseline", settings.QWEN_MODEL_DEBATE)],
    )

_SYSTEM = """You are a professor's admissions assistant. A prospective graduate \
student has sent the outreach below. Decide, on the professor's behalf, whether to \
INVITE them to talk, REQUEST MORE INFO, or DECLINE.

This is a hard judgment — reason it through step by step before answering. Think \
carefully and do NOT skip steps; a wrong call is expensive (a fabricated claim \
waved through, or a strong candidate wrongly turned away).

Work through this reasoning explicitly before you decide:
1. RESEARCH FIT. Use the `retrieve_from_professor_corpus` tool — more than once if \
needed — to check whether the candidate's stated area genuinely overlaps the \
professor's OWN published work. Retrieve on each distinct topic the candidate \
raises, not just the first. A vague topical word-match is not a fit; look for a \
real methodological overlap.
2. CLAIM VERIFICATION. For every specific claim the candidate makes ABOUT the \
professor's work (a cited paper, a result, a method), verify it against the corpus. \
A paper the professor never wrote, or a result the corpus contradicts, is a red \
flag — students sometimes fabricate or inflate these. But note: the candidate's OWN \
background (their thesis, their own results) will NOT be in the professor's corpus, \
and that absence is normal, not a red flag — judge their own credentials on their \
face.
3. CAPACITY. Read the declared capacity carefully. If there are no open slots and \
the professor holds at capacity, a genuine fit should be REQUEST_MORE_INFO (park \
them), not INVITE and not DECLINE. But if the candidate is self-funded / brings \
their own fellowship and the hold is about funding, reason about whether that \
overrides the slot constraint.
4. CONFLICTS. If the evidence points in two directions (strong topical fit but a \
contradicted claim; or good fit but a hard capacity blocker), weigh them explicitly \
and say which wins and why.

Decision guide:
- INVITE: genuine, grounded research overlap in the candidate's own background AND \
capacity to take them now.
- REQUEST_MORE_INFO: real potential but a gap — no open slot right now (a capacity \
hold), or a promising-but-thin case needing one more specific fact.
- DECLINE: no real overlap with the professor's actual work, or a claim about the \
professor's work is fabricated/contradicted, or the outreach is generic with no \
substance.

First write your step-by-step reasoning as plain text (the four steps above). THEN, \
on a final line, output ONLY the JSON verdict, nothing after it:
{"label": "invite|request_more_info|decline", "rationale": "<the decisive reasoning, \
grounded in what the corpus did or did not support>", "drafted_reply": "<a short, \
professional email reply to the candidate>"}
"""


def _candidate_block(outreach: Outreach, professor: Professor) -> str:
    profile = outreach.extracted_profile
    claims = [c.text for c in outreach.extracted_claims]
    cap = professor.capacity
    return (
        f"PROFESSOR: {professor.display_name or professor.email}"
        f" — institution: {professor.institution or 'n/a'}\n"
        f"DECLARED CAPACITY: open_slots={cap.open_slots}, "
        f"students_committed={cap.students_committed}, "
        f"holds_when_at_capacity={cap.hold_when_at_capacity}, "
        f"recruiting_topics={cap.recruiting_topics}\n"
        f"CUSTOM INSTRUCTIONS: {professor.custom_instructions or 'none'}\n\n"
        f"CANDIDATE: {outreach.sender_name or outreach.sender_email}\n"
        f"SUBJECT: {outreach.subject or '(none)'}\n"
        f"STATED INTERESTS: {profile.interests if profile else []}\n"
        f"STATED CREDENTIALS: {profile.credentials if profile else []}\n"
        f"CLAIMS TO VERIFY: {claims}\n\n"
        f"OUTREACH BODY:\n{outreach.body}\n"
    )


def _parse_ruling(content: str) -> Decision:
    """Coerce the agent's final message into a Decision. The agent reasons in prose
    first (chain-of-thought) and emits the JSON verdict last, so parse the LAST
    balanced {...} object in the text rather than the first — the reasoning above it
    may itself contain braces."""
    text = content.strip()
    end = text.rfind("}")
    start = text.rfind("{", 0, end) if end != -1 else -1
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
        label = DecisionLabel(str(data["label"]).strip().lower())
        return Decision(
            label=label,
            rationale=str(data.get("rationale", "")),
            drafted_reply=data.get("drafted_reply"),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Baseline agent produced unparseable verdict, defaulting: {}", exc)
        return Decision(
            label=DecisionLabel.REQUEST_MORE_INFO,
            rationale=f"Unparseable agent output: {content[:200]}",
        )


async def run_baseline(
    outreach: Outreach,
    professor: Professor,
    retriever: PublicationRetriever,
) -> Decision:
    """Run the single-agent control and return its verdict.

    A tool-call loop (bounded by _BASELINE_TOOL_ROUNDS) lets the agent retrieve on
    each topic and verify each claim, reasoning step by step, then it emits a final
    verdict. Generous limits by design — this is the strongest single agent, the
    honest control the society must beat.
    """
    tool: BaseTool = retriever.as_tool()
    model = _baseline_model()
    bound = model.bind_tools([tool])

    messages: list[BaseMessage] = [
        HumanMessage(content=_SYSTEM + "\n\n" + _candidate_block(outreach, professor))
    ]

    response = await bound.ainvoke(messages)
    for _ in range(_BASELINE_TOOL_ROUNDS):
        if not isinstance(response, AIMessage) or not response.tool_calls:
            break
        messages.append(response)
        for tool_call in response.tool_calls:
            try:
                result = await tool.ainvoke(tool_call.get("args") or {})
            except Exception as exc:  # noqa: BLE001 — a failed tool call shouldn't abort the run
                logger.warning("Baseline tool {} failed: {}", tool_call["name"], exc)
                result = {"error": f"Tool failed: {exc}"}
            messages.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=tool_call["id"] or "",
                )
            )
        response = await bound.ainvoke(messages)

    if isinstance(response, AIMessage) and response.tool_calls:
        # Tool budget exhausted mid-loop — force a plain-text final verdict.
        messages.append(response)
        messages.append(
            HumanMessage(content="Tool budget exhausted. Give your final JSON verdict now.")
        )
        response = await model.ainvoke(messages)

    return _parse_ruling(str(response.content))
