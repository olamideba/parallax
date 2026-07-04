from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.application.ports.outbound.email import InboundEmail
from src.application.use_cases.process_inbound_email import ProcessInboundEmailUseCase
from src.domain.models.outreach import Outreach, OutreachStatus
from src.domain.models.professor import Professor


class FakeOutreachRepo:
    def __init__(self, existing: list[Outreach] | None = None) -> None:
        self._existing = existing or []
        self.saved: list[Outreach] = []

    async def get_by_provider_message_id(self, provider_message_id: str):  # noqa: ANN001
        return next(
            (o for o in self._existing if o.provider_message_id == provider_message_id), None
        )

    async def find_recent_duplicate(
        self, professor_id, sender_email, subject, body, since  # noqa: ANN001
    ):
        for o in self._existing + self.saved:
            if (
                o.professor_id == professor_id
                and o.sender_email == sender_email
                and o.subject == subject
                and o.body == body
                and o.received_at >= since
            ):
                return o
        return None

    async def save(self, outreach):  # noqa: ANN001
        self.saved.append(outreach)
        return outreach


class FakeProfessorRepo:
    def __init__(self, professor: Professor | None) -> None:
        self._professor = professor

    async def get_by_intake_email(self, intake_email):  # noqa: ANN001
        return self._professor


class FakeGateway:
    async def fetch_attachments(self, email_id):  # noqa: ANN001
        return []


class FakeObjectStorage:
    async def upload(self, storage_key, data, content_type="application/pdf"):  # noqa: ANN001
        return storage_key

    async def download(self, storage_key):  # noqa: ANN001
        return b""


def _professor() -> Professor:
    return Professor(id=uuid4(), email="prof@uni.edu", intake_email="prof-intake@parallax.dev")


def _inbound(**overrides) -> InboundEmail:  # noqa: ANN003
    base = dict(
        recipient="prof-intake@parallax.dev",
        sender_email="student@uni.edu",
        subject="PhD inquiry",
        text_body="I work on AI safety.",
        provider_message_id="msg_abc123",
    )
    base.update(overrides)
    return InboundEmail(**base)


def _existing_outreach(professor_id, **overrides) -> Outreach:  # noqa: ANN001
    base = dict(
        id=uuid4(),
        professor_id=professor_id,
        sender_email="student@uni.edu",
        subject="PhD inquiry",
        body="I work on AI safety.",
        provider_message_id="msg_abc123",
        received_at=datetime.now(UTC),
        status=OutreachStatus.PENDING_TRIAGE,
    )
    base.update(overrides)
    return Outreach(**base)


@pytest.mark.asyncio
async def test_creates_outreach_on_first_delivery() -> None:
    professor = _professor()
    repo = FakeOutreachRepo()
    uc = ProcessInboundEmailUseCase(
        repo, FakeProfessorRepo(professor), FakeGateway(), FakeObjectStorage()
    )

    outreach = await uc.execute(_inbound())

    assert outreach is not None
    assert len(repo.saved) == 1
    assert outreach.provider_message_id == "msg_abc123"


@pytest.mark.asyncio
async def test_redelivered_webhook_for_same_event_does_not_duplicate() -> None:
    professor = _professor()
    existing = _existing_outreach(professor.id)
    repo = FakeOutreachRepo(existing=[existing])
    uc = ProcessInboundEmailUseCase(
        repo, FakeProfessorRepo(professor), FakeGateway(), FakeObjectStorage()
    )

    outreach = await uc.execute(_inbound(provider_message_id="msg_abc123"))

    assert outreach is not None
    assert outreach.id == existing.id
    assert repo.saved == []  # no new row created


@pytest.mark.asyncio
async def test_duplicate_raw_delivery_with_distinct_provider_id_does_not_duplicate() -> None:
    # Simulates an upstream MTA retry: same sender/subject/body, but Resend
    # assigned a *different* provider_message_id to each raw delivery.
    professor = _professor()
    existing = _existing_outreach(
        professor.id,
        provider_message_id="msg_first_delivery",
        received_at=datetime.now(UTC) - timedelta(minutes=2),
    )
    repo = FakeOutreachRepo(existing=[existing])
    uc = ProcessInboundEmailUseCase(
        repo, FakeProfessorRepo(professor), FakeGateway(), FakeObjectStorage()
    )

    outreach = await uc.execute(_inbound(provider_message_id="msg_second_delivery"))

    assert outreach is not None
    assert outreach.id == existing.id
    assert repo.saved == []


@pytest.mark.asyncio
async def test_duplicate_outside_window_creates_new_outreach() -> None:
    professor = _professor()
    existing = _existing_outreach(
        professor.id,
        provider_message_id="msg_old",
        received_at=datetime.now(UTC) - timedelta(minutes=30),
    )
    repo = FakeOutreachRepo(existing=[existing])
    uc = ProcessInboundEmailUseCase(
        repo, FakeProfessorRepo(professor), FakeGateway(), FakeObjectStorage()
    )

    outreach = await uc.execute(_inbound(provider_message_id="msg_new"))

    assert outreach is not None
    assert outreach.id != existing.id
    assert len(repo.saved) == 1


@pytest.mark.asyncio
async def test_unknown_intake_address_returns_none() -> None:
    repo = FakeOutreachRepo()
    uc = ProcessInboundEmailUseCase(
        repo, FakeProfessorRepo(None), FakeGateway(), FakeObjectStorage()
    )

    outreach = await uc.execute(_inbound())

    assert outreach is None
    assert repo.saved == []
