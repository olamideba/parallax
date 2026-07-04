from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, Relationship, SQLModel
from uuid6 import uuid7


def _now_column() -> Column:
    # A fresh Column instance per call — a `Column` object can only ever be
    # attached to one Table, so this must NOT be hoisted onto a shared mixin
    # inherited by multiple `table=True` classes (that's exactly the "Column
    # object already assigned to Table" error). Each table below calls this
    # itself to get its own Column.
    return Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)


class UUIDBase(SQLModel):
    id: UUID = Field(
        default_factory=lambda: uuid7(),
        primary_key=True,
        nullable=False,
        index=True,
    )


class ProfessorRecord(SQLModel, table=True):
    __tablename__ = "professors"

    # id comes from auth.users.id — never generated here
    id: UUID = Field(primary_key=True, nullable=False, index=True)
    email: str = Field(unique=True, index=True, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    intake_email: str | None = Field(default=None, unique=True, index=True, max_length=320)
    open_slots: int = Field(default=0)
    students_committed: int = Field(default=0)
    budget_amount: int | None = Field(default=None)
    funding_source: str | None = Field(default=None)
    recruiting_topics: str = Field(default="[]")
    gatekeeper_aggressiveness: float = Field(default=0.5)
    auto_resolve_declines: bool = Field(default=True)
    hold_when_at_capacity: bool = Field(default=True)
    custom_instructions: str | None = Field(default=None)
    institution: str | None = Field(default=None, max_length=255)
    institution_country: str | None = Field(default=None, max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())

    publications: list["PublicationRecord"] = Relationship(back_populates="professor")
    outreaches: list["OutreachRecord"] = Relationship(back_populates="professor")


class PublicationRecord(UUIDBase, table=True):
    __tablename__ = "publications"

    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    title: str | None = Field(default=None)
    doi: str | None = Field(default=None)
    url: str | None = Field(default=None)
    storage_key: str | None = Field(default=None)
    indexed: bool = Field(default=False)
    # Lifecycle: pending | indexing | indexed | needs_upload | failed
    status: str = Field(default="pending", max_length=20, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())

    professor: Optional["ProfessorRecord"] = Relationship(back_populates="publications")
    chunks: list["PublicationChunkRecord"] = Relationship(
        back_populates="publication",
        sa_relationship_kwargs={"passive_deletes": True},
    )


class PublicationChunkRecord(UUIDBase, table=True):
    __tablename__ = "publication_chunks"

    publication_id: UUID = Field(foreign_key="publications.id", index=True)
    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    chunk_text: str
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(1024)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())

    publication: Optional["PublicationRecord"] = Relationship(back_populates="chunks")


class OutreachRecord(UUIDBase, table=True):
    __tablename__ = "outreaches"

    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    channel: str = Field(default="email", max_length=50)
    sender_email: str = Field(max_length=255, index=True)
    sender_name: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None)
    body: str
    body_html: str | None = Field(default=None)
    attachment_keys: str = Field(default="[]")
    provider_message_id: str | None = Field(default=None, max_length=255, index=True)
    received_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    status: str = Field(default="pending_triage", max_length=30, index=True)
    replied_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    triage_verdict: str | None = Field(default=None, max_length=20)
    triage_reason: str | None = Field(default=None)
    debate_trace_id: UUID | None = Field(default=None, index=True)
    decision_label: str | None = Field(default=None, max_length=30)
    decision_rationale: str | None = Field(default=None)
    drafted_reply: str | None = Field(default=None)
    overridden_by_professor: bool = Field(default=False)
    extracted_profile_json: str | None = Field(default=None)
    extracted_claims_json: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())

    professor: Optional["ProfessorRecord"] = Relationship(back_populates="outreaches")


class DebateTraceRecord(UUIDBase, table=True):
    __tablename__ = "debate_traces"

    outreach_id: UUID = Field(foreign_key="outreaches.id", index=True)
    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    round_cap: int
    terminated_at_round: int | None = Field(default=None)
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    ended_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    turns_json: str = Field(default="[]")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=_now_column())
