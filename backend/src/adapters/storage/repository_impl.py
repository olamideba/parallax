from __future__ import annotations

from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.ports.outbound.repository import (
    DebateTraceRepository,
    OutreachRepository,
    ProfessorRepository,
)
from src.domain.models.outreach import Outreach, TriageVerdict
from src.domain.models.professor import Professor
from src.domain.models.society import DebateTrace


class SqlOutreachRepository(OutreachRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, outreach: Outreach) -> Outreach:
        raise NotImplementedError

    async def get_by_id(self, outreach_id: UUID) -> Outreach | None:
        raise NotImplementedError

    async def list_by_verdict(
        self, professor_id: UUID, verdict: TriageVerdict | None = None
    ) -> list[Outreach]:
        raise NotImplementedError


class SqlProfessorRepository(ProfessorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, professor: Professor) -> Professor:
        raise NotImplementedError

    async def get_by_id(self, professor_id: UUID) -> Professor | None:
        raise NotImplementedError

    async def get_by_email(self, email: str) -> Professor | None:
        raise NotImplementedError


class SqlDebateTraceRepository(DebateTraceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, trace: DebateTrace) -> DebateTrace:
        raise NotImplementedError

    async def get_by_outreach_id(self, outreach_id: UUID) -> DebateTrace | None:
        raise NotImplementedError
