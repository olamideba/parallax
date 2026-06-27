from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.models.outreach import Outreach, TriageVerdict
from src.domain.models.professor import Professor
from src.domain.models.society import DebateTrace


class OutreachRepository(ABC):
    @abstractmethod
    async def save(self, outreach: Outreach) -> Outreach:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, outreach_id: UUID) -> Outreach | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_verdict(
        self, professor_id: UUID, verdict: TriageVerdict | None = None
    ) -> list[Outreach]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_channel(self, professor_id: UUID, channel: str) -> list[Outreach]:
        raise NotImplementedError


class ProfessorRepository(ABC):
    @abstractmethod
    async def save(self, professor: Professor) -> Professor:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, professor_id: UUID) -> Professor | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Professor | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_intake_email(self, intake_email: str) -> Professor | None:
        raise NotImplementedError


class DebateTraceRepository(ABC):
    @abstractmethod
    async def save(self, trace: DebateTrace) -> DebateTrace:
        raise NotImplementedError

    @abstractmethod
    async def get_by_outreach_id(self, outreach_id: UUID) -> DebateTrace | None:
        raise NotImplementedError
