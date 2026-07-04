from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

EMAIL_CHANNEL = "email"
SYSTEM_CONFIRMATION_CHANNEL = "system_confirmation"


class OutreachStatus(StrEnum):
    PENDING_TRIAGE = "pending_triage"
    HELD = "held"  # promoted, but debate deferred because the professor is at capacity
    REJECTED = "rejected"  # auto-resolved clear decline (no HITL) — visible + reversible
    AWAITING_REVIEW = "awaiting_review"
    REPLIED = "replied"


class TriageVerdict(StrEnum):
    REJECT = "reject"
    PROMOTE = "promote"


class DecisionLabel(StrEnum):
    INVITE = "invite"
    REQUEST_MORE_INFO = "request_more_info"
    DECLINE = "decline"


class Attachment(BaseModel):
    """An outreach attachment persisted to object storage (e.g. a candidate CV)."""

    storage_key: str
    filename: str
    content_type: str | None = None


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
    subject: str | None = None
    body: str
    body_html: str | None = None
    attachment_keys: list[Attachment] = Field(default_factory=list)
    # The inbound provider's id for this specific received-email event (e.g.
    # Resend's `email_id`). Lets ingestion recognize a redelivered webhook for
    # the same event before minting a duplicate Outreach.
    provider_message_id: str | None = None
    received_at: datetime
    status: OutreachStatus = OutreachStatus.PENDING_TRIAGE
    replied_at: datetime | None = None

    extracted_profile: ExtractedProfile | None = None
    extracted_claims: list[ExtractedClaim] = Field(default_factory=list)
    triage_verdict: TriageVerdict | None = None
    # The Gatekeeper's one-sentence justification for the verdict. Kept for both
    # verdicts so the debate can open with *why* this outreach was let through.
    triage_reason: str | None = None
    debate_trace_id: UUID | None = None
    decision: Decision | None = None
    # True creation time — carried through every read/save round trip (a
    # fresh value here would get pushed into the DB on the next update, since
    # the repository reconstructs and merges a new record on every save()).
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
