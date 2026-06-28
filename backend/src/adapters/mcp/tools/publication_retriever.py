from __future__ import annotations

from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.ingestion.vector_index import PgVectorStore
from src.application.ports.outbound.llm_client import LLMClient


async def retrieve_publications(
    session: AsyncSession,
    llm_client: LLMClient,
    professor_id: UUID,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Fetch relevant publication chunks for a query from the professor's corpus."""
    embedding = await llm_client.embed(query)
    store = PgVectorStore(session)
    return await store.query(embedding=embedding, professor_id=professor_id, top_k=top_k)
