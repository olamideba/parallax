from __future__ import annotations

from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.ports.outbound.vector_store import VectorStore


class PgVectorStore(VectorStore):
    """pgvector-backed implementation using the publication_chunks table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, doc_id: UUID, text: str, embedding: list[float], metadata: dict) -> None:
        raise NotImplementedError

    async def query(
        self,
        embedding: list[float],
        professor_id: UUID,
        top_k: int = 5,
    ) -> list[dict]:
        raise NotImplementedError
