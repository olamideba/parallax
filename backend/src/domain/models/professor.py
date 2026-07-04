from __future__ import annotations

from datetime import UTC, datetime
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
    # True creation time — round-tripped through every read/save (see the
    # matching comment on Outreach.created_at for why this must not default
    # to "now" on every save).
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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
    # Optional — used by the Assessor as the mobility-lookup destination and by
    # the debate for context. When unset, agents skip destination-specific
    # checks rather than guessing.
    institution: str | None = None
    institution_country: str | None = None
    # Free-text directive the professor sets at onboarding to steer the agent
    # society (e.g. "only theory students, no pure-applied ML"). Injected into
    # the Gatekeeper prompt and, later, the debate agents.
    custom_instructions: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
