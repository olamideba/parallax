import pytest

from src.domain.collaboration.negotiation_engine import NegotiationEngine


def test_negotiation_engine_instantiates():
    engine = NegotiationEngine(round_cap=3)
    assert engine.round_cap == 3


def test_negotiation_engine_respects_round_cap():
    engine = NegotiationEngine(round_cap=5)
    assert engine.round_cap == 5


@pytest.mark.asyncio
async def test_negotiation_engine_run_not_implemented():
    from uuid import uuid4
    from datetime import datetime, timezone
    from src.domain.models.outreach import Outreach, OutreachStatus

    engine = NegotiationEngine(round_cap=3)
    outreach = Outreach(
        id=uuid4(),
        professor_id=uuid4(),
        sender_email="student@example.com",
        body="I am interested in your work.",
        received_at=datetime.now(timezone.utc),
        status=OutreachStatus.PENDING_TRIAGE,
    )
    with pytest.raises(NotImplementedError):
        await engine.run(outreach, professor_id=outreach.professor_id)
