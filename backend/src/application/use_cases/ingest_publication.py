from __future__ import annotations

from uuid import UUID

from loguru import logger
from uuid6 import uuid7

from src.application.ports.outbound.llm_client import LLMClient
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.ports.outbound.publication_source import (
    ArxivGateway,
    DoiGateway,
    PdfFetcher,
    PdfTextExtractor,
)
from src.application.ports.outbound.repository import PublicationRepository
from src.application.ports.outbound.vector_store import VectorStore
from src.config import get_settings
from src.domain.exceptions.base import IngestionError, NotFoundError
from src.domain.models.professor import Publication, PublicationStatus
from src.domain.services.chunking import chunk_text


class IngestPublicationUseCase:
    """Resolve a publication's source PDF, chunk + embed it, and index to pgvector.

    Source resolution priority:
      1. storage_key  -> uploaded PDF in object storage (foundation path)
      2. arxiv url    -> derive PDF url, fetch, enrich metadata
      3. direct url   -> fetch the PDF as-is
      4. doi          -> Unpaywall OA PDF (+ Crossref metadata); else needs_upload

    Every collaborator is an outbound port, so the use case knows nothing about
    R2, PyMuPDF, httpx, arXiv/Unpaywall, or SQL.
    """

    def __init__(
        self,
        publication_repo: PublicationRepository,
        object_storage: ObjectStorage,
        pdf_fetcher: PdfFetcher,
        pdf_extractor: PdfTextExtractor,
        arxiv_gateway: ArxivGateway,
        doi_gateway: DoiGateway,
        llm_client: LLMClient,
        vector_store: VectorStore,
    ) -> None:
        self._pubs = publication_repo
        self._storage = object_storage
        self._fetcher = pdf_fetcher
        self._extractor = pdf_extractor
        self._arxiv = arxiv_gateway
        self._doi = doi_gateway
        self._llm = llm_client
        self._vector_store = vector_store

    async def execute(self, publication_id: UUID) -> Publication:
        pub = await self._pubs.get(publication_id)
        if pub is None:
            raise NotFoundError(f"Publication {publication_id} not found")

        pub.status = PublicationStatus.INDEXING
        pub.indexed = False
        pub = await self._pubs.save(pub)

        try:
            text = await self._resolve_text(pub)
        except _NeedsUpload as exc:
            logger.info("Publication {} needs manual upload: {}", publication_id, exc.reason)
            return await self._finalize(pub, PublicationStatus.NEEDS_UPLOAD)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ingestion failed for publication {}: {}", publication_id, exc)
            return await self._finalize(pub, PublicationStatus.FAILED)

        if not text.strip():
            return await self._finalize(pub, PublicationStatus.FAILED)

        try:
            await self._index_text(pub, text)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Indexing failed for publication {}: {}", publication_id, exc)
            return await self._finalize(pub, PublicationStatus.FAILED)

        return await self._finalize(pub, PublicationStatus.INDEXED, indexed=True)

    # --- source resolution ---

    async def _resolve_text(self, pub: Publication) -> str:
        if pub.storage_key:
            data = await self._storage.download(pub.storage_key)
            return self._extractor.extract_text(data)

        if self._arxiv.is_arxiv_url(pub.url):
            assert pub.url is not None
            meta = await self._arxiv.resolve(pub.url)
            if meta.title and not pub.title:
                pub.title = meta.title
            if not meta.pdf_url:
                raise IngestionError(f"arXiv resolution yielded no PDF for {pub.url}")
            data = await self._fetcher.fetch(meta.pdf_url)
            return self._extractor.extract_text(data)

        if pub.url:
            data = await self._fetcher.fetch(pub.url)
            return self._extractor.extract_text(data)

        if pub.doi:
            meta = await self._doi.resolve(pub.doi)
            if meta.title and not pub.title:
                pub.title = meta.title
            if not meta.pdf_url:
                raise _NeedsUpload("No open-access PDF available for this DOI")
            data = await self._fetcher.fetch(meta.pdf_url)
            return self._extractor.extract_text(data)

        raise IngestionError("Publication has no storage_key, url, or doi to ingest")

    # --- indexing ---

    async def _index_text(self, pub: Publication, text: str) -> None:
        settings = get_settings()
        chunks = chunk_text(
            text,
            chunk_size=settings.INGEST_CHUNK_SIZE,
            overlap=settings.INGEST_CHUNK_OVERLAP,
        )
        if not chunks:
            raise IngestionError("No chunks produced from extracted text")

        # Idempotency: clear any prior chunks for this publication.
        await self._pubs.clear_chunks(pub.id)

        for chunk in chunks:
            embedding = await self._llm.embed(chunk)
            await self._vector_store.upsert(
                doc_id=uuid7(),
                text=chunk,
                embedding=embedding,
                metadata={
                    "publication_id": pub.id,
                    "professor_id": pub.professor_id,
                },
            )
        logger.info("Indexed {} chunks for publication {}", len(chunks), pub.id)

    async def _finalize(
        self,
        pub: Publication,
        status: PublicationStatus,
        indexed: bool = False,
    ) -> Publication:
        pub.status = status
        pub.indexed = indexed
        return await self._pubs.save(pub)


class _NeedsUpload(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
