from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class TriageVerdict(StrEnum):
    REJECT = "reject"
    PROMOTE = "promote"


class DecisionLabel(StrEnum):
    INVITE = "invite"
    REQUEST_MORE_INFO = "request_more_info"
    DECLINE = "decline"


class ExtractedClaim(BaseModel):
    text: str
    verified: bool | None = None
    receipt: str | None = None


class ExtractedProfile(BaseModel):
    name: str | None = None
    email: str | None = None
    interests: list[str] = Field(default_factory=list)
    credentials: list[str] = Field(default_factory=list)
    funding_context: str | None = None
    country: str | None = None


class Decision(BaseModel):
    label: DecisionLabel
    rationale: str
    drafted_reply: str | None = None
    overridden_by_professor: bool = False


class Outreach(BaseModel):
    id: UUID
    professor_id: UUID
    channel: str = "email"
    sender_email: str
    sender_name: str | None = None
    body: str
    attachment_keys: list[str] = Field(default_factory=list)
    received_at: datetime

    extracted_profile: ExtractedProfile | None = None
    extracted_claims: list[ExtractedClaim] = Field(default_factory=list)
    triage_verdict: TriageVerdict | None = None
    debate_trace_id: UUID | None = None
    decision: Decision | None = None
