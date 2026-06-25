from __future__ import annotations

from uuid import UUID

from src.application.ports.outbound.llm_client import LLMClient
from src.application.ports.outbound.mcp_tool_bus import McpToolBus
from src.application.ports.outbound.repository import (
    DebateTraceRepository,
    OutreachRepository,
    ProfessorRepository,
)
from src.application.ports.outbound.vector_store import VectorStore
from src.domain.models.outreach import Outreach
from src.domain.models.society import DebateTrace


class EvaluateCandidateUseCase:
    """Runs the multi-round simultaneous debate society and produces a DebateTrace + Decision."""

    def __init__(
        self,
        outreach_repo: OutreachRepository,
        professor_repo: ProfessorRepository,
        trace_repo: DebateTraceRepository,
        llm_client: LLMClient,
        vector_store: VectorStore,
        mcp_bus: McpToolBus,
        round_cap: int,
    ) -> None:
        self._outreach_repo = outreach_repo
        self._professor_repo = professor_repo
        self._trace_repo = trace_repo
        self._llm = llm_client
        self._vector_store = vector_store
        self._mcp_bus = mcp_bus
        self._round_cap = round_cap

    async def execute(self, outreach_id: UUID, professor_id: UUID) -> tuple[DebateTrace, Outreach]:
        raise NotImplementedError
