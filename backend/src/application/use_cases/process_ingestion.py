from __future__ import annotations

from uuid import UUID

from src.application.ports.outbound.llm_client import LLMClient
from src.application.ports.outbound.repository import OutreachRepository
from src.application.ports.outbound.vector_store import VectorStore
from src.domain.models.outreach import Outreach


class ProcessIngestionUseCase:
    """Deep-parses a promoted Outreach: populates extracted_profile and extracted_claims."""

    def __init__(
        self,
        outreach_repo: OutreachRepository,
        llm_client: LLMClient,
        vector_store: VectorStore,
    ) -> None:
        self._outreach_repo = outreach_repo
        self._llm = llm_client
        self._vector_store = vector_store

    async def execute(self, outreach_id: UUID, professor_id: UUID) -> Outreach:
        raise NotImplementedError
