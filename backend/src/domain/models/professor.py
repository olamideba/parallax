from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class PublicationStatus(StrEnum):
    """Lifecycle states for a publication's ingestion."""

    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    NEEDS_UPLOAD = "needs_upload"
    FAILED = "failed"


class Publication(BaseModel):
    id: UUID
    professor_id: UUID
    title: str | None = None
    doi: str | None = None
    url: str | None = None
    storage_key: str | None = None
    indexed: bool = False
    status: PublicationStatus = PublicationStatus.PENDING


class Capacity(BaseModel):
    open_slots: int = 0
    students_committed: int = 0
    budget_amount: int | None = None
    funding_source: str | None = None
    recruiting_topics: list[str] = Field(default_factory=list)
    auto_resolve_declines: bool = True
    hold_when_at_capacity: bool = True


class Professor(BaseModel):
    id: UUID
    email: str
    display_name: str | None = None
    intake_email: str | None = None
    capacity: Capacity = Field(default_factory=Capacity)
    publications: list[Publication] = Field(default_factory=list)
    gatekeeper_aggressiveness: float = Field(default=0.5, ge=0.0, le=1.0)
