from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.domain.models.outreach import (
    DecisionLabel,
    ExtractedClaim,
    ExtractedProfile,
    Decision,
    Outreach,
    OutreachStatus,
    TriageVerdict,
)


def _base_outreach(**kwargs) -> Outreach:
    defaults = dict(
        id=uuid4(),
        professor_id=uuid4(),
        sender_email="student@example.com",
        body="I am interested in your research.",
        received_at=datetime.now(timezone.utc),
    )
    return Outreach(**{**defaults, **kwargs})


# --- OutreachStatus ---

def test_default_status_is_pending_triage():
    outreach = _base_outreach()
    assert outreach.status == OutreachStatus.PENDING_TRIAGE


def test_status_values_are_strings():
    assert OutreachStatus.PENDING_TRIAGE == "pending_triage"
    assert OutreachStatus.REJECTED == "rejected"
    assert OutreachStatus.AWAITING_REVIEW == "awaiting_review"
    assert OutreachStatus.REPLIED == "replied"


# --- TriageVerdict / DecisionLabel ---

def test_triage_verdict_values():
    assert TriageVerdict.REJECT == "reject"
    assert TriageVerdict.PROMOTE == "promote"


def test_decision_label_values():
    assert DecisionLabel.INVITE == "invite"
    assert DecisionLabel.REQUEST_MORE_INFO == "request_more_info"
    assert DecisionLabel.DECLINE == "decline"


# --- ExtractedClaim ---

def test_extracted_claim_defaults():
    claim = ExtractedClaim(text="I published in NeurIPS.")
    assert claim.verified is None
    assert claim.receipt is None


def test_extracted_claim_with_receipt():
    claim = ExtractedClaim(text="I know transformers.", verified=True, receipt="chunk:abc123")
    assert claim.verified is True
    assert claim.receipt == "chunk:abc123"


# --- ExtractedProfile ---

def test_extracted_profile_defaults():
    profile = ExtractedProfile()
    assert profile.name is None
    assert profile.email is None
    assert profile.interests == []
    assert profile.credentials == []
    assert profile.funding_context is None
    assert profile.country is None


def test_extracted_profile_with_data():
    profile = ExtractedProfile(
        name="Ada Lovelace",
        email="ada@example.com",
        interests=["ML", "HCI"],
        credentials=["PhD Stanford"],
        country="UK",
    )
    assert profile.name == "Ada Lovelace"
    assert len(profile.interests) == 2


# --- Decision ---

def test_decision_not_overridden_by_default():
    decision = Decision(label=DecisionLabel.INVITE, rationale="Strong fit.")
    assert decision.overridden_by_professor is False
    assert decision.drafted_reply is None


def test_decision_override_flag():
    decision = Decision(
        label=DecisionLabel.DECLINE,
        rationale="No capacity.",
        overridden_by_professor=True,
    )
    assert decision.overridden_by_professor is True


# --- Outreach ---

def test_outreach_defaults():
    outreach = _base_outreach()
    assert outreach.channel == "email"
    assert outreach.attachment_keys == []
    assert outreach.extracted_claims == []
    assert outreach.extracted_profile is None
    assert outreach.triage_verdict is None
    assert outreach.debate_trace_id is None
    assert outreach.decision is None
    assert outreach.replied_at is None


def test_outreach_with_triage_verdict():
    outreach = _base_outreach(triage_verdict=TriageVerdict.PROMOTE)
    assert outreach.triage_verdict == TriageVerdict.PROMOTE


def test_outreach_with_claims():
    claims = [
        ExtractedClaim(text="Published in ICML.", verified=True, receipt="chunk:001"),
        ExtractedClaim(text="NSF-funded.", verified=None),
    ]
    outreach = _base_outreach(extracted_claims=claims)
    assert len(outreach.extracted_claims) == 2
    assert outreach.extracted_claims[0].receipt == "chunk:001"


def test_outreach_with_decision():
    decision = Decision(
        label=DecisionLabel.INVITE,
        rationale="Great match.",
        drafted_reply="Dear student, welcome!",
    )
    outreach = _base_outreach(
        status=OutreachStatus.AWAITING_REVIEW,
        decision=decision,
    )
    assert outreach.status == OutreachStatus.AWAITING_REVIEW
    assert outreach.decision.label == DecisionLabel.INVITE
