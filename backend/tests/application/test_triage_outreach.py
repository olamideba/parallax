from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.ports.outbound.gatekeeper import Gatekeeper, GatekeeperAssessment
from src.application.use_cases.triage_outreach import TriageOutreachUseCase
from src.domain.models.outreach import (
    Attachment,
    DecisionLabel,
    ExtractedProfile,
    Outreach,
    OutreachStatus,
    TriageVerdict,
)
from src.domain.models.professor import Capacity, Professor


class FakeOutreachRepo:
    def __init__(self, outreach: Outreach | None) -> None:
        self._outreach = outreach
        self.saved: Outreach | None = None

    async def get_by_id(self, outreach_id):  # noqa: ANN001
        return self._outreach

    async def save(self, outreach):  # noqa: ANN001
        self.saved = outreach
        return outreach


class FakeProfessorRepo:
    def __init__(self, professor: Professor | None) -> None:
        self._professor = professor

    async def get_by_id(self, professor_id):  # noqa: ANN001
        return self._professor


class FakeObjectStorage:
    def __init__(self, data: bytes = b"%PDF-1.4 fake") -> None:
        self._data = data
        self.downloaded: list[str] = []

    async def download(self, storage_key: str) -> bytes:
        self.downloaded.append(storage_key)
        return self._data

    async def upload(self, *args, **kwargs):  # pragma: no cover - unused here
        return ""


class FakeExtractor:
    def extract_text(self, data: bytes) -> str:
        return "Extracted CV: published at NeurIPS 2025."


class FakeGatekeeper(Gatekeeper):
    def __init__(self, assessment: GatekeeperAssessment) -> None:
        self.assessment = assessment
        self.last_kwargs: dict | None = None

    async def assess(self, **kwargs) -> GatekeeperAssessment:  # noqa: ANN003
        self.last_kwargs = kwargs
        return self.assessment


def _outreach(**overrides) -> Outreach:  # noqa: ANN003
    base = dict(
        id=uuid4(),
        professor_id=uuid4(),
        sender_email="student@uni.edu",
        subject="Prospective PhD",
        body="I work on AI safety and alignment.",
        received_at=datetime.now(UTC),
        status=OutreachStatus.PENDING_TRIAGE,
    )
    base.update(overrides)
    return Outreach(**base)


def _professor(pid, **overrides) -> Professor:  # noqa: ANN001, ANN003
    return Professor(
        id=pid,
        email="prof@uni.edu",
        capacity=Capacity(recruiting_topics=["AI safety"]),
        custom_instructions="Only theory students.",
        **overrides,
    )


@pytest.mark.asyncio
async def test_promote_sets_profile_and_leaves_pending() -> None:
    outreach = _outreach()
    prof = _professor(outreach.professor_id)
    gk = FakeGatekeeper(
        GatekeeperAssessment(
            verdict=TriageVerdict.PROMOTE,
            reason="Clear AI-safety alignment.",
            profile=ExtractedProfile(name="Jonathan Vance"),
            claim_texts=["published at NeurIPS 2025"],
        )
    )
    repo = FakeOutreachRepo(outreach)
    uc = TriageOutreachUseCase(
        repo, FakeProfessorRepo(prof), FakeObjectStorage(), FakeExtractor(), gk
    )

    verdict = await uc.execute(outreach.id)

    assert verdict == TriageVerdict.PROMOTE
    assert repo.saved is not None
    assert repo.saved.status == OutreachStatus.PENDING_TRIAGE
    assert repo.saved.decision is None
    assert repo.saved.extracted_profile.name == "Jonathan Vance"
    assert repo.saved.extracted_claims[0].text == "published at NeurIPS 2025"
    # Professor context reached the gatekeeper.
    assert gk.last_kwargs["custom_instructions"] == "Only theory students."
    assert gk.last_kwargs["professor_topics"] == ["AI safety"]


@pytest.mark.asyncio
async def test_reject_synthesizes_decline_and_awaits_review() -> None:
    outreach = _outreach()
    prof = _professor(outreach.professor_id)
    gk = FakeGatekeeper(
        GatekeeperAssessment(
            verdict=TriageVerdict.REJECT,
            reason="Mass-mailed, no awareness of the professor's work.",
        )
    )
    repo = FakeOutreachRepo(outreach)
    uc = TriageOutreachUseCase(
        repo, FakeProfessorRepo(prof), FakeObjectStorage(), FakeExtractor(), gk
    )

    verdict = await uc.execute(outreach.id)

    assert verdict == TriageVerdict.REJECT
    assert repo.saved.status == OutreachStatus.AWAITING_REVIEW
    assert repo.saved.decision.label == DecisionLabel.DECLINE
    assert "Filtered at triage" in repo.saved.decision.rationale


@pytest.mark.asyncio
async def test_pdf_attachment_text_is_extracted_and_passed() -> None:
    outreach = _outreach(
        attachment_keys=[Attachment(storage_key="outreach/x/cv.pdf", filename="cv.pdf")]
    )
    prof = _professor(outreach.professor_id)
    gk = FakeGatekeeper(
        GatekeeperAssessment(verdict=TriageVerdict.PROMOTE, reason="ok")
    )
    storage = FakeObjectStorage()
    uc = TriageOutreachUseCase(
        FakeOutreachRepo(outreach), FakeProfessorRepo(prof), storage, FakeExtractor(), gk
    )

    await uc.execute(outreach.id)

    assert storage.downloaded == ["outreach/x/cv.pdf"]
    assert "NeurIPS" in gk.last_kwargs["cv_text"]


@pytest.mark.asyncio
async def test_already_triaged_is_noop() -> None:
    outreach = _outreach(
        status=OutreachStatus.AWAITING_REVIEW, triage_verdict=TriageVerdict.PROMOTE
    )
    repo = FakeOutreachRepo(outreach)
    gk = FakeGatekeeper(GatekeeperAssessment(verdict=TriageVerdict.REJECT, reason="x"))
    uc = TriageOutreachUseCase(
        repo, FakeProfessorRepo(None), FakeObjectStorage(), FakeExtractor(), gk
    )

    verdict = await uc.execute(outreach.id)

    assert verdict == TriageVerdict.PROMOTE
    assert repo.saved is None  # nothing re-saved
    assert gk.last_kwargs is None  # gatekeeper never called
