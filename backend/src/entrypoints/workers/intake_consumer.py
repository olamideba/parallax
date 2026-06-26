from __future__ import annotations

from src.entrypoints.workers.celery_app import celery_app


@celery_app.task(name="parallax.intake.triage_and_ingest", bind=True, max_retries=3)
def triage_and_ingest(self, outreach_id: str, professor_id: str) -> dict:
    """Gatekeeper triage → deep ingestion → debate → arbitrator decision."""
    raise NotImplementedError


@celery_app.task(name="parallax.intake.run_debate", bind=True, max_retries=3)
def run_debate(self, outreach_id: str, professor_id: str) -> dict:
    """Runs the multi-round simultaneous debate society for a promoted outreach."""
    raise NotImplementedError
