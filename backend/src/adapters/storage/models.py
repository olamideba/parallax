from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel
from uuid6 import uuid7


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
    open_slots: int = Field(default=0)
    students_committed: int = Field(default=0)
    budget_context: str | None = Field(default=None)
    recruiting_topics: str = Field(default="[]")
    gatekeeper_aggressiveness: float = Field(default=0.5)

    publications: list[PublicationRecord] = Relationship(back_populates="professor")
    outreaches: list[OutreachRecord] = Relationship(back_populates="professor")


class PublicationRecord(UUIDBase, table=True):
    __tablename__ = "publications"

    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    title: str | None = Field(default=None)
    doi: str | None = Field(default=None)
    url: str | None = Field(default=None)
    storage_key: str | None = Field(default=None)
    indexed: bool = Field(default=False)

    professor: ProfessorRecord | None = Relationship(back_populates="publications")
    chunks: list[PublicationChunkRecord] = Relationship(back_populates="publication")


class PublicationChunkRecord(UUIDBase, table=True):
    __tablename__ = "publication_chunks"

    publication_id: UUID = Field(foreign_key="publications.id", index=True)
    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    chunk_text: str
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(1536)))

    publication: PublicationRecord | None = Relationship(back_populates="chunks")


class OutreachRecord(UUIDBase, table=True):
    __tablename__ = "outreaches"

    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    channel: str = Field(default="email", max_length=50)
    sender_email: str = Field(max_length=255, index=True)
    sender_name: str | None = Field(default=None, max_length=255)
    body: str
    attachment_keys: str = Field(default="[]")
    received_at: datetime
    triage_verdict: str | None = Field(default=None, max_length=20)
    debate_trace_id: UUID | None = Field(default=None, index=True)
    decision_label: str | None = Field(default=None, max_length=30)
    decision_rationale: str | None = Field(default=None)
    drafted_reply: str | None = Field(default=None)
    overridden_by_professor: bool = Field(default=False)
    extracted_profile_json: str | None = Field(default=None)
    extracted_claims_json: str | None = Field(default=None)

    professor: ProfessorRecord | None = Relationship(back_populates="outreaches")


class DebateTraceRecord(UUIDBase, table=True):
    __tablename__ = "debate_traces"

    outreach_id: UUID = Field(foreign_key="outreaches.id", index=True)
    professor_id: UUID = Field(foreign_key="professors.id", index=True)
    round_cap: int
    terminated_at_round: int | None = Field(default=None)
    started_at: datetime
    ended_at: datetime | None = Field(default=None)
    turns_json: str = Field(default="[]")
