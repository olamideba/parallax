from __future__ import annotations

import asyncio
from uuid import UUID

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.ingestion.parsers.pdf_parser import PyMuPdfTextExtractor
from src.adapters.ingestion.vector_index import PgVectorStore
from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.adapters.orchestration.langgraph_engine import LangGraphNegotiationEngine
from src.adapters.qwen_cloud.gatekeeper import QwenGatekeeper
from src.adapters.qwen_cloud.reranker import QwenReranker
from src.adapters.qwen_cloud.runtime import QwenLLMClient
from src.adapters.storage.database import dispose_engine, session_factory
from src.adapters.storage.object_storage import R2ObjectStorage
from src.adapters.storage.repository_impl import (
    SqlDebateTraceRepository,
    SqlOutreachRepository,
    SqlProfessorRepository,
    SqlPublicationRepository,
)
from src.application.use_cases.run_debate import RunDebateUseCase
from src.application.use_cases.triage_outreach import TriageOutreachUseCase
from src.config import get_settings
from src.domain.collaboration.negotiation_engine import NegotiationEngine
from src.domain.models.outreach import TriageVerdict
from src.domain.models.professor import Professor
from src.entrypoints.workers.celery_app import celery_app


async def _run_triage(outreach_id: UUID) -> TriageVerdict | None:
    try:
        async with session_factory()() as session:
            use_case = TriageOutreachUseCase(
                outreach_repo=SqlOutreachRepository(session),
                professor_repo=SqlProfessorRepository(session),
                object_storage=R2ObjectStorage(),
                pdf_extractor=PyMuPdfTextExtractor(),
                gatekeeper=QwenGatekeeper(),
            )
            return await use_case.execute(outreach_id)
    finally:
        # See dispose_engine() docstring: the cached engine must not survive
        # past this task's event loop, or the next task in this worker
        # process will crash reusing a pool bound to a closed loop.
        await dispose_engine()


@celery_app.task(name="parallax.intake.triage_and_ingest", bind=True, max_retries=3)
def triage_and_ingest(self, outreach_id: str, professor_id: str) -> dict:
    """Gatekeeper triage. Promotes survivors to the debate; rejects are queued
    for the professor as a triage-filtered decline."""
    try:
        verdict = asyncio.run(_run_triage(UUID(outreach_id)))
    except Exception as exc:  # noqa: BLE001
        logger.exception("triage_and_ingest failed for {}", outreach_id)
        raise self.retry(exc=exc, countdown=30) from exc

    if verdict == TriageVerdict.PROMOTE:
        run_debate.delay(outreach_id, professor_id)

    return {"outreach_id": outreach_id, "verdict": verdict.value if verdict else None}


def _build_engine(professor: Professor, session: AsyncSession) -> NegotiationEngine:
    settings = get_settings()
    llm = QwenLLMClient()
    # Reranking is optional — only wire it when a workspace is configured;
    # otherwise the retriever falls back to raw vector-similarity order.
    reranker = QwenReranker() if settings.DASHSCOPE_WORKSPACE_ID else None
    retriever = PublicationRetriever(
        llm_client=llm,
        vector_store=PgVectorStore(session),
        publication_repo=SqlPublicationRepository(session),
        professor_id=professor.id,
        reranker=reranker,
    )
    return LangGraphNegotiationEngine(
        round_cap=settings.DEBATE_ROUND_CAP, retriever=retriever
    )


async def _run_debate(outreach_id: UUID) -> str | None:
    try:
        async with session_factory()() as session:
            use_case = RunDebateUseCase(
                outreach_repo=SqlOutreachRepository(session),
                professor_repo=SqlProfessorRepository(session),
                trace_repo=SqlDebateTraceRepository(session),
                engine_factory=lambda professor: _build_engine(professor, session),
            )
            trace_id = await use_case.execute(outreach_id)
            return str(trace_id) if trace_id else None
    finally:
        # See dispose_engine() docstring.
        await dispose_engine()


@celery_app.task(name="parallax.intake.run_debate", bind=True, max_retries=3)
def run_debate(self, outreach_id: str, professor_id: str) -> dict:
    """Runs the multi-round simultaneous debate society for a promoted outreach."""
    try:
        trace_id = asyncio.run(_run_debate(UUID(outreach_id)))
    except Exception as exc:  # noqa: BLE001
        logger.exception("run_debate failed for {}", outreach_id)
        raise self.retry(exc=exc, countdown=30) from exc

    return {"outreach_id": outreach_id, "debate_trace_id": trace_id}
