"""Throwaway instrumentation: run ONE case through both paths and dump everything —
full baseline message log + full society DebateTrace (every turn, every role, every
receipt/action) + the exact rendered prompt each debate role saw. Not part of the
benchmark suite; delete after use.

Usage (from backend/):
    DATABASE_URL=... QWEN_MODEL_*=... uv run python -m tests.benchmark.deep_dive_one_case <case_id>
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from src.adapters.ingestion.vector_index import PgVectorStore
from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.adapters.orchestration.langgraph_engine import LangGraphNegotiationEngine
from src.adapters.qwen_cloud.personas import DEBATER_PERSONAS, first_name, persona_for
from src.adapters.qwen_cloud.reranker import QwenReranker
from src.adapters.qwen_cloud.runtime import QwenLLMClient
from src.adapters.qwen_cloud.templates import render_prompt
from src.adapters.storage.database import dispose_engine, session_factory
from src.adapters.storage.repository_impl import SqlPublicationRepository
from src.config import get_settings
from src.domain.models.society import AgentRole
from tests.benchmark.baseline_agent import _SYSTEM, _baseline_model, _candidate_block, _parse_ruling
from tests.benchmark.cases import case_by_id, professor_for_case
from tests.benchmark.run_benchmark import _seed_professor

_OUT = Path(__file__).parent / "out" / "deep_dive.md"


async def _run_baseline_verbose(outreach, professor, retriever) -> tuple[str, list[dict]]:
    """Same logic as run_baseline, but returns the full message transcript."""
    tool = retriever.as_tool()
    model = _baseline_model()
    bound = model.bind_tools([tool])
    messages: list[BaseMessage] = [
        HumanMessage(content=_SYSTEM + "\n\n" + _candidate_block(outreach, professor))
    ]
    log: list[dict] = [{"role": "system+human", "content": messages[0].content}]

    response = await bound.ainvoke(messages)
    for _ in range(4):
        if not isinstance(response, AIMessage) or not response.tool_calls:
            break
        log.append(
            {
                "role": "assistant(tool_call)",
                "content": str(response.content),
                "tool_calls": response.tool_calls,
            }
        )
        messages.append(response)
        for tc in response.tool_calls:
            result = await tool.ainvoke(tc.get("args") or {})
            log.append(
                {
                    "role": "tool_result",
                    "tool": tc["name"],
                    "args": tc.get("args"),
                    "result": result,
                }
            )
            messages.append(
                ToolMessage(content=json.dumps(result, default=str), tool_call_id=tc["id"] or "")
            )
        response = await bound.ainvoke(messages)

    log.append({"role": "assistant(final)", "content": str(response.content)})
    decision = _parse_ruling(str(response.content))
    return decision.label.value, log


async def main(case_id: str) -> None:
    case = case_by_id(case_id)
    sp = professor_for_case(case)
    settings = get_settings()

    lines = [f"# Deep dive: `{case_id}`\n", f"**Expected label:** `{case.expected_label}`\n"]
    lines.append(f"**Candidate email:**\n```\n{case.body}\n```\n")
    lines.append(f"**Claims:** {case.claims}\n")

    # --- rendered prompts for every debate role, up front ---
    lines.append("\n## System prompts (rendered, for this professor)\n")
    roles = (
        AgentRole.GATEKEEPER,
        AgentRole.ADVOCATE,
        AgentRole.AUDITOR,
        AgentRole.ASSESSOR,
        AgentRole.ARBITRATOR,
    )
    for role in roles:
        template = {
            AgentRole.GATEKEEPER: "gatekeeper_opening.j2",
            AgentRole.ADVOCATE: "advocate.j2",
            AgentRole.AUDITOR: "auditor.j2",
            AgentRole.ASSESSOR: "assessor.j2",
            AgentRole.ARBITRATOR: "arbitrator.j2",
        }[role]
        try:
            rendered = render_prompt(
                template,
                prior_turns=[],
                triage_reason="(n/a — prompt preview)",
                round_cap=settings.DEBATE_ROUND_CAP,
                persona=persona_for(role),
                custom_instructions=sp.professor.custom_instructions,
                cast=DEBATER_PERSONAS,
                professor_first_name=first_name(sp.professor.display_name),
                extracted_profile=case.__dict__,
                extracted_claims=[{"text": c} for c in case.claims],
                capacity=sp.professor.capacity,
                institution=sp.professor.institution,
                institution_country=sp.professor.institution_country,
                recruiting_topics=sp.professor.capacity.recruiting_topics,
                publication_chunks=[],
            )
        except Exception as exc:  # noqa: BLE001 — best-effort preview
            rendered = f"(render failed: {exc})"
        lines.append(f"\n### {role.value.upper()} ({template})\n```\n{rendered}\n```\n")

    async with session_factory()() as session:
        llm = QwenLLMClient()
        reranker = QwenReranker() if settings.DASHSCOPE_WORKSPACE_ID else None
        retriever = PublicationRetriever(
            llm_client=llm,
            vector_store=PgVectorStore(session),
            publication_repo=SqlPublicationRepository(session),
            professor_id=sp.professor.id,
            reranker=reranker,
        )
        await _seed_professor(sp, session)
        outreach = case.to_outreach(sp.professor.id)

        # --- baseline, verbose ---
        lines.append("\n## PATH A — Single-agent baseline (full transcript)\n")
        base_label, base_log = await _run_baseline_verbose(outreach, sp.professor, retriever)
        for entry in base_log:
            dumped = json.dumps(entry, indent=2, default=str)[:4000]
            lines.append(f"\n**[{entry['role']}]**\n```\n{dumped}\n```\n")
        lines.append(f"\n**BASELINE FINAL LABEL: `{base_label}`**\n")

        # --- society, verbose ---
        lines.append("\n## PATH B — Society (full debate trace)\n")
        engine = LangGraphNegotiationEngine(
            round_cap=settings.DEBATE_ROUND_CAP, retriever=retriever
        )
        outcome = await engine.run(outreach, sp.professor)
        for turn in outcome.trace.turns:
            lines.append(f"\n### [Round {turn.round}] {turn.role.value.upper()}\n")
            lines.append(f"```\n{turn.content}\n```\n")
            if turn.receipts:
                for r in turn.receipts:
                    lines.append(f"- RECEIPT: *{r.source_title}* — \"{r.chunk_text[:200]}\"\n")
            if turn.actions:
                for a in turn.actions:
                    lines.append(f"- ACTION: {a.kind} `{a.name}` — {a.detail}\n")
        lines.append(f"\n**SOCIETY FINAL LABEL: `{outcome.decision.label.value}`**\n")
        lines.append(f"\n**SOCIETY RATIONALE:**\n```\n{outcome.decision.rationale}\n```\n")

    Path(_OUT).write_text("\n".join(lines))
    print(f"Wrote {_OUT}")
    await dispose_engine()


if __name__ == "__main__":
    case_id = sys.argv[1] if len(sys.argv) > 1 else "mata-strong-1"
    asyncio.run(main(case_id))
