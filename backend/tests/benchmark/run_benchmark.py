"""Single-agent vs. agent-society benchmark runner (Track 3 efficiency gain).

Runs both paths over the same labeled cases and the same per-professor RAG corpus,
then writes machine-readable results and an honest Markdown report.

  Path A (baseline): one agent, same tools, no society   -> tests/benchmark/baseline_agent.py
  Path B (society):  the real LangGraph debate pipeline   -> src/adapters/orchestration

The claim it substantiates is NOT speed or raw cost (the society is slower and
pricier per case). It is accuracy — specifically, catching fabricated/inflated
claims and capacity mismatches a lone agent rubber-stamps — at a stated token/$ cost.

Requires live Postgres (pgvector) + live DashScope. Reads all endpoints/keys from
`.env` via get_settings(). Run from backend/:

    uv run python -m tests.benchmark.run_benchmark
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from loguru import logger
from uuid6 import uuid7

from src.adapters.ingestion.vector_index import PgVectorStore
from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.adapters.orchestration.langgraph_engine import LangGraphNegotiationEngine
from src.adapters.qwen_cloud.reranker import QwenReranker
from src.adapters.qwen_cloud.runtime import QwenLLMClient
from src.adapters.qwen_cloud.token_logging import reset_token_totals, token_totals
from src.adapters.storage.database import dispose_engine, session_factory
from src.adapters.storage.repository_impl import (
    SqlProfessorRepository,
    SqlPublicationRepository,
)
from src.config import get_settings
from src.domain.models.professor import Publication, PublicationStatus
from src.domain.services.chunking import chunk_text
from tests.benchmark import pricing
from tests.benchmark.baseline_agent import run_baseline
from tests.benchmark.cases import (
    CASES,
    BenchmarkCase,
    SyntheticProfessor,
    synthetic_professors,
)

_OUT_DIR = Path(__file__).parent / "out"


# --- per-path result rows -----------------------------------------------------


@dataclass
class PathResult:
    label: str
    correct: bool
    false_accept: bool
    input_tokens: int
    output_tokens: int
    total_tokens: int
    llm_calls: int
    latency_s: float
    cost_usd: float | None
    rationale: str


@dataclass
class CaseResult:
    case_id: str
    professor_key: str
    failure_mode: str
    expected_label: str
    baseline: PathResult
    society: PathResult
    error: str | None = None


# --- corpus seeding -----------------------------------------------------------


async def _seed_professor(sp: SyntheticProfessor, session) -> PublicationRetriever:  # noqa: ANN001
    """Persist the synthetic professor + embed its publications into pgvector,
    then build the same retriever the debate worker builds. Idempotent by design:
    re-running upserts the professor and re-embeds chunks under fresh ids (old
    rows for the fixed professor_id are cleared first)."""
    settings = get_settings()
    llm = QwenLLMClient()
    prof_repo = SqlProfessorRepository(session)
    pub_repo = SqlPublicationRepository(session)
    vector_store = PgVectorStore(session)

    await prof_repo.save(sp.professor)
    logger.info("Seeded professor '{}' ({} pubs)", sp.key, len(sp.publications))

    for idx, syn_pub in enumerate(sp.publications):
        pub = Publication(
            id=UUID(int=(sp.professor.id.int + idx + 1)),
            professor_id=sp.professor.id,
            title=syn_pub.title,
            status=PublicationStatus.INDEXED,
            indexed=True,
        )
        await pub_repo.save(pub)
        await pub_repo.clear_chunks(pub.id)
        chunks = chunk_text(
            syn_pub.text,
            chunk_size=settings.INGEST_CHUNK_SIZE,
            overlap=settings.INGEST_CHUNK_OVERLAP,
        )
        for chunk in chunks:
            embedding = await llm.embed(chunk)
            await vector_store.upsert(
                doc_id=uuid7(),
                text=chunk,
                embedding=embedding,
                metadata={"publication_id": pub.id, "professor_id": sp.professor.id},
            )
    await session.commit()

    reranker = QwenReranker() if settings.DASHSCOPE_WORKSPACE_ID else None
    return PublicationRetriever(
        llm_client=llm,
        vector_store=vector_store,
        publication_repo=pub_repo,
        professor_id=sp.professor.id,
        reranker=reranker,
    )


# --- running one path with a token bracket ------------------------------------


def _score(case: BenchmarkCase, label: str) -> tuple[bool, bool]:
    correct = label == case.expected_label
    # A false accept: the trap was a fabricated/inflated claim (truth = decline)
    # and the path let it through as a positive/soft outcome.
    false_accept = case.is_accept_trap() and label in {"invite", "request_more_info"}
    return correct, false_accept


def _path_result(
    case: BenchmarkCase, label: str, latency_s: float, totals: dict, model: str
) -> PathResult:
    correct, false_accept = _score(case, label)
    in_tok, out_tok = totals["input"], totals["output"]
    return PathResult(
        label=label,
        correct=correct,
        false_accept=false_accept,
        input_tokens=in_tok,
        output_tokens=out_tok,
        total_tokens=in_tok + out_tok,
        llm_calls=totals["calls"],
        latency_s=round(latency_s, 2),
        cost_usd=pricing.cost_usd(model, in_tok, out_tok),
        rationale="",
    )


async def _run_case(
    case: BenchmarkCase, sp: SyntheticProfessor, retriever: PublicationRetriever
) -> CaseResult:
    settings = get_settings()

    # --- Path A: single agent ---
    reset_token_totals()
    t0 = time.perf_counter()
    outreach = case.to_outreach(sp.professor.id)
    baseline_decision = await run_baseline(outreach, sp.professor, retriever)
    base_latency = time.perf_counter() - t0
    base = _path_result(
        case,
        baseline_decision.label.value,
        base_latency,
        token_totals(),
        settings.QWEN_MODEL_DEBATE,
    )
    base.rationale = baseline_decision.rationale[:400]

    # --- Path B: the society ---
    reset_token_totals()
    t0 = time.perf_counter()
    engine = LangGraphNegotiationEngine(
        round_cap=settings.DEBATE_ROUND_CAP, retriever=retriever
    )
    outcome = await engine.run(outreach, sp.professor)
    soc_latency = time.perf_counter() - t0
    soc_totals = token_totals()
    soc = _path_result(
        case,
        outcome.decision.label.value,
        soc_latency,
        soc_totals,
        settings.QWEN_MODEL_DEBATE,  # blended at the debater rate; see pricing.blended_cost_usd
    )
    soc.rationale = outcome.decision.rationale[:400]

    logger.info(
        "  {} | truth={} | baseline={}{} | society={}{}",
        case.case_id,
        case.expected_label,
        base.label,
        " ✗" if not base.correct else " ✓",
        soc.label,
        " ✗" if not soc.correct else " ✓",
    )
    return CaseResult(
        case_id=case.case_id,
        professor_key=case.professor_key,
        failure_mode=case.failure_mode,
        expected_label=case.expected_label,
        baseline=base,
        society=soc,
    )


# --- aggregation + reporting --------------------------------------------------


def _summary(results: list[CaseResult]) -> dict:
    ok = [r for r in results if r.error is None]
    n = len(ok)

    def agg(path: str) -> dict:
        rows = [getattr(r, path) for r in ok]
        priced = [r.cost_usd for r in rows if r.cost_usd is not None]
        return {
            "accuracy": round(sum(r.correct for r in rows) / n, 3) if n else None,
            "correct": sum(r.correct for r in rows),
            "false_accepts": sum(r.false_accept for r in rows),
            "total_tokens": sum(r.total_tokens for r in rows),
            "total_llm_calls": sum(r.llm_calls for r in rows),
            "total_latency_s": round(sum(r.latency_s for r in rows), 1),
            "total_cost_usd": round(sum(priced), 4) if priced else None,
        }

    return {"n": n, "baseline": agg("baseline"), "society": agg("society")}


def _headline(s: dict) -> str:
    b, soc, n = s["baseline"], s["society"], s["n"]
    caught = b["false_accepts"] - soc["false_accepts"]
    tok_mult = (
        round(soc["total_tokens"] / b["total_tokens"], 1)
        if b["total_tokens"]
        else float("nan")
    )
    return (
        f"On {n} labeled cases, the single-agent baseline scored "
        f"{b['accuracy']:.0%} accuracy and let {b['false_accepts']} "
        f"fabricated/inflated-claim case(s) through; the society scored "
        f"{soc['accuracy']:.0%} and let {soc['false_accepts']} through — "
        f"catching {caught} the baseline missed, at {tok_mult}× the tokens "
        f"({soc['total_tokens']:,} vs {b['total_tokens']:,})."
    )


def _write_reports(results: list[CaseResult], summary: dict, label: str | None = None) -> None:
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat()
    suffix = f"_{label}" if label else ""

    (_OUT_DIR / f"results{suffix}.json").write_text(
        json.dumps(
            {"generated_at": stamp, "summary": summary, "cases": [asdict(r) for r in results]},
            indent=2,
        )
    )

    b, soc = summary["baseline"], summary["society"]

    def cost(v: float | None) -> str:
        return f"${v:.4f}" if v is not None else "N/A"

    lines = [
        "# Agent Society vs. Single-Agent Baseline",
        "",
        f"_Generated {stamp}. {summary['n']} labeled cases, identical RAG corpus per "
        "professor, same retrieval tool available to both paths._",
        "",
        "## Headline",
        "",
        _headline(summary),
        "",
        "The society is **not** cheaper or faster — it spends more tokens and wall-clock "
        "to buy accuracy on exactly the cases a lone agent rubber-stamps. That trade is "
        "the point.",
        "",
        "## Summary",
        "",
        "| Metric | Single-agent | Society |",
        "| :-- | --: | --: |",
        f"| Accuracy | {b['accuracy']:.0%} | {soc['accuracy']:.0%} |",
        f"| Correct / {summary['n']} | {b['correct']} | {soc['correct']} |",
        f"| False accepts (trap missed) | {b['false_accepts']} | {soc['false_accepts']} |",
        f"| Total tokens | {b['total_tokens']:,} | {soc['total_tokens']:,} |",
        f"| Total LLM calls | {b['total_llm_calls']} | {soc['total_llm_calls']} |",
        f"| Total latency (s) | {b['total_latency_s']} | {soc['total_latency_s']} |",
        f"| Est. cost (USD) | {cost(b['total_cost_usd'])} | {cost(soc['total_cost_usd'])} |",
        "",
        "## Per-case",
        "",
        "| Case | Failure mode | Truth | Baseline | Society |",
        "| :-- | :-- | :-- | :-- | :-- |",
    ]
    for r in results:
        if r.error:
            lines.append(f"| {r.case_id} | {r.failure_mode} | {r.expected_label} | ERROR | ERROR |")
            continue
        bmark = "✓" if r.baseline.correct else "✗"
        smark = "✓" if r.society.correct else "✗"
        lines.append(
            f"| {r.case_id} | {r.failure_mode} | {r.expected_label} | "
            f"{r.baseline.label} {bmark} | {r.society.label} {smark} |"
        )
    lines += [
        "",
        "> Cost is estimated at the debater-tier rate on the Singapore endpoint; unpriced "
        "models report N/A. See `pricing.py` — verify rates against the live pricing page "
        "before quoting dollar figures.",
        "",
    ]
    (_OUT_DIR / f"report{suffix}.md").write_text("\n".join(lines))
    logger.info(
        "Wrote {} and {}",
        _OUT_DIR / f"results{suffix}.json",
        _OUT_DIR / f"report{suffix}.md",
    )


# --- entrypoint ---------------------------------------------------------------


async def run(case_filter: set[str] | None = None, label: str | None = None) -> dict:
    """Seed corpora, run both paths over every case, write reports, return summary."""
    selected = [c for c in CASES if case_filter is None or c.case_id in case_filter]
    profs = {sp.key: sp for sp in synthetic_professors()}
    results: list[CaseResult] = []

    try:
        async with session_factory()() as session:
            retrievers: dict[str, PublicationRetriever] = {}
            needed_keys = {c.professor_key for c in selected}
            for key in needed_keys:
                retrievers[key] = await _seed_professor(profs[key], session)

            for case in selected:
                sp = profs[case.professor_key]
                try:
                    results.append(await _run_case(case, sp, retrievers[case.professor_key]))
                except Exception as exc:  # noqa: BLE001 — one bad case shouldn't sink the run
                    logger.exception("Case {} failed", case.case_id)
                    results.append(
                        CaseResult(
                            case_id=case.case_id,
                            professor_key=case.professor_key,
                            failure_mode=case.failure_mode,
                            expected_label=case.expected_label,
                            baseline=_empty_path(),
                            society=_empty_path(),
                            error=str(exc),
                        )
                    )
    finally:
        await dispose_engine()

    summary = _summary(results)
    _write_reports(results, summary, label)
    logger.info("\n{}", _headline(summary))
    return summary


def _empty_path() -> PathResult:
    return PathResult(
        label="error",
        correct=False,
        false_accept=False,
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        llm_calls=0,
        latency_s=0.0,
        cost_usd=None,
        rationale="",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agent-society benchmark.")
    parser.add_argument(
        "--cases", nargs="*", help="Restrict to these case_ids (default: all)."
    )
    parser.add_argument(
        "--label", help="Suffix for output files, e.g. --label v2 -> report_v2.md."
    )
    args = parser.parse_args()
    case_filter = set(args.cases) if args.cases else None
    asyncio.run(run(case_filter, args.label))


if __name__ == "__main__":
    main()
