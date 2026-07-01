from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.use_cases.run_debate import RunDebateUseCase
from src.domain.collaboration.negotiation_engine import DebateOutcome
from src.domain.models.outreach import (
    Decision,
    DecisionLabel,
    Outreach,
    OutreachStatus,
    TriageVerdict,
)
from src.domain.models.professor import Professor
from src.domain.models.society import DebateTrace


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


class FakeTraceRepo:
    def __init__(self) -> None:
        self.saved: DebateTrace | None = None

    async def save(self, trace):  # noqa: ANN001
        self.saved = trace
        return trace


class FakeEngine:
    def __init__(self, outcome: DebateOutcome) -> None:
        self._outcome = outcome
        self.ran_with: tuple | None = None

    async def run(self, outreach, professor):  # noqa: ANN001
        self.ran_with = (outreach, professor)
        return self._outcome


def _outreach(**overrides) -> Outreach:  # noqa: ANN003
    base = dict(
        id=uuid4(),
        professor_id=uuid4(),
        sender_email="s@uni.edu",
        body="hi",
        received_at=datetime.now(UTC),
        status=OutreachStatus.PENDING_TRIAGE,
        triage_verdict=TriageVerdict.PROMOTE,
    )
    base.update(overrides)
    return Outreach(**base)


def _outcome(outreach: Outreach, professor: Professor) -> DebateOutcome:
    trace = DebateTrace(
        id=uuid4(),
        outreach_id=outreach.id,
        professor_id=professor.id,
        round_cap=3,
        started_at=datetime.now(UTC),
    )
    decision = Decision(label=DecisionLabel.INVITE, rationale="fit", drafted_reply="hello")
    return DebateOutcome(trace=trace, decision=decision)


def _professor(pid) -> Professor:  # noqa: ANN001
    return Professor(id=pid, email="p@uni.edu")


@pytest.mark.asyncio
async def test_promoted_outreach_runs_debate_persists_trace_and_decision() -> None:
    outreach = _outreach()
    prof = _professor(outreach.professor_id)
    outcome = _outcome(outreach, prof)
    engine = FakeEngine(outcome)
    o_repo, t_repo = FakeOutreachRepo(outreach), FakeTraceRepo()

    uc = RunDebateUseCase(o_repo, FakeProfessorRepo(prof), t_repo, lambda p: engine)
    trace_id = await uc.execute(outreach.id)

    assert trace_id == outcome.trace.id
    assert t_repo.saved is outcome.trace
    assert o_repo.saved.status == OutreachStatus.AWAITING_REVIEW
    assert o_repo.saved.decision.label == DecisionLabel.INVITE
    assert o_repo.saved.debate_trace_id == outcome.trace.id
    assert engine.ran_with[1] is prof


@pytest.mark.asyncio
async def test_already_reviewed_outreach_is_noop() -> None:
    existing_trace_id = uuid4()
    outreach = _outreach(status=OutreachStatus.AWAITING_REVIEW, debate_trace_id=existing_trace_id)
    prof = _professor(outreach.professor_id)
    engine = FakeEngine(_outcome(outreach, prof))
    o_repo, t_repo = FakeOutreachRepo(outreach), FakeTraceRepo()

    uc = RunDebateUseCase(o_repo, FakeProfessorRepo(prof), t_repo, lambda p: engine)
    trace_id = await uc.execute(outreach.id)

    assert trace_id == existing_trace_id
    assert engine.ran_with is None  # engine never ran
    assert t_repo.saved is None
    assert o_repo.saved is None


@pytest.mark.asyncio
async def test_non_promoted_outreach_does_not_debate() -> None:
    outreach = _outreach(triage_verdict=TriageVerdict.REJECT)
    prof = _professor(outreach.professor_id)
    engine = FakeEngine(_outcome(outreach, prof))
    o_repo = FakeOutreachRepo(outreach)

    uc = RunDebateUseCase(o_repo, FakeProfessorRepo(prof), FakeTraceRepo(), lambda p: engine)
    result = await uc.execute(outreach.id)

    assert result is None
    assert engine.ran_with is None


@pytest.mark.asyncio
async def test_missing_outreach_returns_none() -> None:
    uc = RunDebateUseCase(
        FakeOutreachRepo(None), FakeProfessorRepo(None), FakeTraceRepo(), lambda p: None
    )
    assert await uc.execute(uuid4()) is None
