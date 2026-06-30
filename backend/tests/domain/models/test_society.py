from datetime import datetime, timezone
from uuid import uuid4

from src.domain.models.society import AgentRole, DebateTrace, DebateTurn, Receipt


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _turn(round: int, role: AgentRole, content: str = "test content", **kwargs) -> DebateTurn:
    return DebateTurn(round=round, role=role, content=content, created_at=_now(), **kwargs)


# --- AgentRole ---

def test_agent_role_values():
    assert AgentRole.GATEKEEPER == "gatekeeper"
    assert AgentRole.ADVOCATE == "advocate"
    assert AgentRole.AUDITOR == "auditor"
    assert AgentRole.ASSESSOR == "assessor"
    assert AgentRole.ARBITRATOR == "arbitrator"


# --- Receipt ---

def test_receipt_minimal():
    receipt = Receipt(source_title="Attention Is All You Need", chunk_text="We propose a model...")
    assert receipt.relevance_note is None


def test_receipt_with_relevance_note():
    receipt = Receipt(
        source_title="BERT",
        chunk_text="Bidirectional encoder...",
        relevance_note="Directly relevant to candidate's stated interest.",
    )
    assert receipt.relevance_note is not None


# --- DebateTurn ---

def test_debate_turn_defaults():
    turn = _turn(round=1, role=AgentRole.GATEKEEPER)
    assert turn.receipts == []
    assert turn.references_turn_ids == []


def test_debate_turn_with_receipts():
    receipts = [
        Receipt(source_title="Paper A", chunk_text="chunk text A"),
        Receipt(source_title="Paper B", chunk_text="chunk text B"),
    ]
    turn = _turn(round=1, role=AgentRole.ADVOCATE, receipts=receipts)
    assert len(turn.receipts) == 2
    assert turn.receipts[0].source_title == "Paper A"


def test_debate_turn_references_prior_turns():
    turn = _turn(round=2, role=AgentRole.AUDITOR, references_turn_ids=[0, 1])
    assert turn.references_turn_ids == [0, 1]


# --- DebateTrace ---

def test_debate_trace_empty_on_creation():
    trace = DebateTrace(
        id=uuid4(),
        outreach_id=uuid4(),
        professor_id=uuid4(),
        round_cap=3,
        started_at=_now(),
    )
    assert trace.turns == []
    assert trace.terminated_at_round is None
    assert trace.ended_at is None


def test_debate_trace_with_turns():
    turns = [
        _turn(round=1, role=AgentRole.GATEKEEPER, content="Initial triage."),
        _turn(round=1, role=AgentRole.ADVOCATE, content="Candidate is strong."),
        _turn(round=1, role=AgentRole.AUDITOR, content="Claim is unverified."),
    ]
    trace = DebateTrace(
        id=uuid4(),
        outreach_id=uuid4(),
        professor_id=uuid4(),
        round_cap=3,
        started_at=_now(),
        turns=turns,
    )
    assert len(trace.turns) == 3
    roles = {t.role for t in trace.turns}
    assert AgentRole.GATEKEEPER in roles
    assert AgentRole.ADVOCATE in roles
    assert AgentRole.AUDITOR in roles


def test_debate_trace_terminated_round():
    trace = DebateTrace(
        id=uuid4(),
        outreach_id=uuid4(),
        professor_id=uuid4(),
        round_cap=5,
        started_at=_now(),
        terminated_at_round=2,
        ended_at=_now(),
    )
    assert trace.terminated_at_round == 2
    assert trace.terminated_at_round <= trace.round_cap


def test_debate_trace_all_agent_roles_representable():
    # Verify the full society can participate in a single round
    all_roles = list(AgentRole)
    turns = [_turn(round=1, role=role) for role in all_roles]
    trace = DebateTrace(
        id=uuid4(),
        outreach_id=uuid4(),
        professor_id=uuid4(),
        round_cap=1,
        started_at=_now(),
        turns=turns,
    )
    assert len(trace.turns) == len(all_roles)
