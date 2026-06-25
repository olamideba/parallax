from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    GATEKEEPER = "gatekeeper"
    ADVOCATE = "advocate"
    AUDITOR = "auditor"
    ASSESSOR = "assessor"
    ARBITRATOR = "arbitrator"


class Receipt(BaseModel):
    source_title: str
    chunk_text: str
    relevance_note: str | None = None


class DebateTurn(BaseModel):
    round: int
    role: AgentRole
    content: str
    receipts: list[Receipt] = Field(default_factory=list)
    references_turn_ids: list[int] = Field(default_factory=list)
    created_at: datetime


class DebateTrace(BaseModel):
    id: UUID
    outreach_id: UUID
    professor_id: UUID
    turns: list[DebateTurn] = Field(default_factory=list)
    round_cap: int
    terminated_at_round: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
