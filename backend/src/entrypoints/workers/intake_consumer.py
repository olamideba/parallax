from __future__ import annotations

import asyncio
from uuid import UUID

from loguru import logger

from src.adapters.ingestion.parsers.pdf_parser import PyMuPdfTextExtractor
from src.adapters.qwen_cloud.gatekeeper import QwenGatekeeper
from src.adapters.storage.database import session_factory
from src.adapters.storage.object_storage import R2ObjectStorage
from src.adapters.storage.repository_impl import (
    SqlOutreachRepository,
    SqlProfessorRepository,
)
from src.application.use_cases.triage_outreach import TriageOutreachUseCase
from src.domain.models.outreach import TriageVerdict
from src.entrypoints.workers.celery_app import celery_app


async def _run_triage(outreach_id: UUID) -> TriageVerdict | None:
    async with session_factory()() as session:
        use_case = TriageOutreachUseCase(
            outreach_repo=SqlOutreachRepository(session),
            professor_repo=SqlProfessorRepository(session),
            object_storage=R2ObjectStorage(),
            pdf_extractor=PyMuPdfTextExtractor(),
            gatekeeper=QwenGatekeeper(),
        )
        return await use_case.execute(outreach_id)


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


@celery_app.task(name="parallax.intake.run_debate", bind=True, max_retries=3)
def run_debate(self, outreach_id: str, professor_id: str) -> dict:
    """Runs the multi-round simultaneous debate society for a promoted outreach."""
    raise NotImplementedError
