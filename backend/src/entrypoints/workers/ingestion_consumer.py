from __future__ import annotations

import asyncio
from uuid import UUID

from loguru import logger

from src.adapters.ingestion.arxiv_client import ArxivApiGateway
from src.adapters.ingestion.doi_client import DoiApiGateway
from src.adapters.ingestion.parsers.pdf_parser import PyMuPdfTextExtractor
from src.adapters.ingestion.pdf_fetcher import HttpPdfFetcher
from src.adapters.ingestion.vector_index import PgVectorStore
from src.adapters.qwen_cloud.runtime import QwenLLMClient
from src.adapters.storage.database import session_factory
from src.adapters.storage.object_storage import R2ObjectStorage
from src.adapters.storage.repository_impl import SqlPublicationRepository
from src.application.use_cases.ingest_publication import IngestPublicationUseCase
from src.entrypoints.workers.celery_app import celery_app


async def _run(publication_id: UUID) -> str:
    async with session_factory()() as session:
        use_case = IngestPublicationUseCase(
            publication_repo=SqlPublicationRepository(session),
            object_storage=R2ObjectStorage(),
            pdf_fetcher=HttpPdfFetcher(),
            pdf_extractor=PyMuPdfTextExtractor(),
            arxiv_gateway=ArxivApiGateway(),
            doi_gateway=DoiApiGateway(),
            llm_client=QwenLLMClient(),
            vector_store=PgVectorStore(session),
        )
        pub = await use_case.execute(publication_id)
        return pub.status.value


@celery_app.task(name="parallax.ingest.publication", bind=True, max_retries=3)
def ingest_publication(self, publication_id: str) -> dict:
    """Resolve, chunk, embed and index a single publication's PDF."""
    pub_id = UUID(publication_id)
    try:
        status = asyncio.run(_run(pub_id))
    except Exception as exc:  # noqa: BLE001
        logger.exception("ingest_publication task failed for {}", publication_id)
        raise self.retry(exc=exc, countdown=30) from exc
    return {"publication_id": publication_id, "status": status}
