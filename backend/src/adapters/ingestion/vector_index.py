from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.storage.models import PublicationChunkRecord
from src.application.ports.outbound.vector_store import VectorStore


class PgVectorStore(VectorStore):
    """pgvector-backed implementation using the publication_chunks table.

    `metadata` must carry `publication_id` and `professor_id` (UUIDs or their
    str form) so a chunk can be tied back to its publication and owner.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, doc_id: UUID, text: str, embedding: list[float], metadata: dict) -> None:
        publication_id = _as_uuid(metadata["publication_id"])
        professor_id = _as_uuid(metadata["professor_id"])

        existing = await self._session.get(PublicationChunkRecord, doc_id)
        if existing is not None:
            existing.chunk_text = text
            existing.embedding = embedding
            existing.publication_id = publication_id
            existing.professor_id = professor_id
            self._session.add(existing)
        else:
            self._session.add(
                PublicationChunkRecord(
                    id=doc_id,
                    publication_id=publication_id,
                    professor_id=professor_id,
                    chunk_text=text,
                    embedding=embedding,
                )
            )
        await self._session.flush()

    async def query(
        self,
        embedding: list[float],
        professor_id: UUID,
        top_k: int = 5,
    ) -> list[dict]:
        distance = PublicationChunkRecord.embedding.cosine_distance(embedding)  # type: ignore[union-attr]
        stmt = (
            select(PublicationChunkRecord, distance.label("distance"))
            .where(PublicationChunkRecord.professor_id == professor_id)
            .order_by(distance)
            .limit(top_k)
        )
        result = await self._session.exec(stmt)
        rows = result.all()
        return [
            {
                "id": str(chunk.id),
                "publication_id": str(chunk.publication_id),
                "professor_id": str(chunk.professor_id),
                "chunk_text": chunk.chunk_text,
                "distance": float(dist),
                "score": 1.0 - float(dist),
            }
            for chunk, dist in rows
        ]


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))
