from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from src.adapters.orchestration.langgraph_engine import (
    ArbitratorRuling,
    LangGraphNegotiationEngine,
)
from src.domain.models.outreach import (
    ExtractedClaim,
    ExtractedProfile,
    Outreach,
    OutreachStatus,
)
from src.domain.models.professor import Capacity, Professor
from src.domain.models.society import ActionKind, AgentRole

# --- Fakes ---------------------------------------------------------------


class FakeStructured:
    def __init__(self, ruling: ArbitratorRuling) -> None:
        self._ruling = ruling
        self.last_prompt: str | None = None

    async def ainvoke(self, prompt):  # noqa: ANN001
        self.last_prompt = prompt
        return self._ruling


class FakeChatModel:
    """Pops one scripted response per ainvoke call; bind_tools is a no-op."""

    def __init__(self, responses: list, ruling: ArbitratorRuling | None = None) -> None:
        self._responses = responses
        self._structured = FakeStructured(
            ruling
            or ArbitratorRuling(
                label="request_more_info", rationale="default", drafted_reply="dear"
            )
        )

    def bind_tools(self, tools):  # noqa: ANN001
        return self

    def with_structured_output(self, schema):  # noqa: ANN001
        return self._structured

    async def ainvoke(self, messages):  # noqa: ANN001
        if not self._responses:
            return AIMessage(content="PASS")
        item = self._responses.pop(0)
        return AIMessage(content=item) if isinstance(item, str) else item


@tool
def retrieve_from_professor_corpus(query: str) -> list[dict]:
    """Fake corpus retrieval tool (matches the real tool's registered name)."""
    return [
        {"chunk_text": "attention chunk", "source_title": "Attention Paper", "relevance_score": 0.9}
    ]


class FakeRetriever:
    def __init__(self, chunks: list[dict] | None = None) -> None:
        self._chunks = chunks or []
        self.searched_queries: list[str] = []

    async def search(self, query: str):
        self.searched_queries.append(query)

        class _R:
            def __init__(self, d: dict) -> None:
                self._d = d

            def model_dump(self) -> dict:
                return self._d

        return [_R(c) for c in self._chunks]

    def as_tool(self):
        return retrieve_from_professor_corpus


def _outreach() -> Outreach:
    return Outreach(
        id=uuid4(),
        professor_id=uuid4(),
        sender_email="student@uni.edu",
        subject="PhD inquiry",
        body="I work on AI safety.",
        received_at=datetime.now(UTC),
        status=OutreachStatus.PENDING_TRIAGE,
        extracted_profile=ExtractedProfile(name="Jon", interests=["AI safety"]),
        extracted_claims=[ExtractedClaim(text="published at NeurIPS 2025")],
    )


def _professor(pid) -> Professor:  # noqa: ANN001
    return Professor(
        id=pid,
        email="prof@uni.edu",
        capacity=Capacity(open_slots=2, students_committed=1, recruiting_topics=["AI safety"]),
        institution="Test University",
        institution_country="United States",
    )


def _engine(models: dict, round_cap: int = 3, retriever: FakeRetriever | None = None):
    def factory(role):  # noqa: ANN001
        return models[role]

    return LangGraphNegotiationEngine(
        round_cap=round_cap,
        retriever=retriever or FakeRetriever(),
        chat_model_factory=factory,
    )


def _ruling(label: str = "invite") -> ArbitratorRuling:
    return ArbitratorRuling(
        label=label,
        rationale="Strong fit per [REF:0].",
        drafted_reply="Dear Jon, ...",
    )


# --- Tests ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_pass_after_round_one_terminates_early() -> None:
    models = {
        AgentRole.ADVOCATE: FakeChatModel(["Alignment is real.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["Claim 1: VERIFIED — ok.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["One slot open.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling("invite")),
    }
    outreach = _outreach()
    outcome = await _engine(models, round_cap=3).run(outreach, _professor(outreach.professor_id))

    roles = [t.role for t in outcome.trace.turns]
    assert roles.count(AgentRole.ARBITRATOR) == 1
    # 3 debater turns in round 1, none in round 2 (all passed).
    debater_turns = [t for t in outcome.trace.turns if t.role != AgentRole.ARBITRATOR]
    assert len(debater_turns) == 3
    assert all(t.round == 1 for t in debater_turns)
    assert outcome.trace.terminated_at_round == 1
    assert outcome.decision.label == "invite"
    assert outcome.decision.drafted_reply == "Dear Jon, ..."


@pytest.mark.asyncio
async def test_round_cap_terminates_persistent_disagreement() -> None:
    talk = ["arguing"] * 10  # never passes
    models = {
        AgentRole.ADVOCATE: FakeChatModel(list(talk)),
        AgentRole.AUDITOR: FakeChatModel(list(talk)),
        AgentRole.ASSESSOR: FakeChatModel(list(talk)),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling("request_more_info")),
    }
    outreach = _outreach()
    outcome = await _engine(models, round_cap=2).run(outreach, _professor(outreach.professor_id))

    debater_turns = [t for t in outcome.trace.turns if t.role != AgentRole.ARBITRATOR]
    assert len(debater_turns) == 6  # 3 debaters x 2 rounds, hard stop
    assert outcome.trace.terminated_at_round == 2
    assert outcome.trace.round_cap == 2


@pytest.mark.asyncio
async def test_receipts_and_references_are_parsed_from_content() -> None:
    advocate_text = (
        'Fit is genuine [RECEIPT: "Attention Paper", "the exact excerpt"]. See [REF:0].'
    )
    models = {
        AgentRole.ADVOCATE: FakeChatModel([advocate_text, "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["capacity fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling()),
    }
    outreach = _outreach()
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    advocate_turn = next(t for t in outcome.trace.turns if t.role == AgentRole.ADVOCATE)
    assert advocate_turn.receipts[0].source_title == "Attention Paper"
    assert advocate_turn.receipts[0].chunk_text == "the exact excerpt"
    # Round 1 has no prior turns, so REF:0 is out of range and dropped.
    assert advocate_turn.references_turn_ids == []


@pytest.mark.asyncio
async def test_second_round_references_resolve_against_transcript() -> None:
    models = {
        AgentRole.ADVOCATE: FakeChatModel(["opening case.", "Rebutting [REF:1]."]),
        AgentRole.AUDITOR: FakeChatModel(["opening audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["opening assessment.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling()),
    }
    outreach = _outreach()
    outcome = await _engine(models, round_cap=2).run(outreach, _professor(outreach.professor_id))

    round2 = [t for t in outcome.trace.turns if t.round == 2 and t.role == AgentRole.ADVOCATE]
    assert len(round2) == 1
    assert round2[0].references_turn_ids == [1]


@pytest.mark.asyncio
async def test_tool_calls_record_actions_and_receipts() -> None:
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "retrieve_from_professor_corpus",
                "args": {"query": "AI safety"},
                "id": "tc-1",
            }
        ],
    )
    models = {
        AgentRole.ADVOCATE: FakeChatModel([tool_call_msg, "Found strong overlap.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling()),
    }
    outreach = _outreach()
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    advocate_turn = next(t for t in outcome.trace.turns if t.role == AgentRole.ADVOCATE)
    assert advocate_turn.content == "Found strong overlap."
    assert len(advocate_turn.actions) == 1
    assert advocate_turn.actions[0].kind == ActionKind.RETRIEVAL
    assert advocate_turn.actions[0].name == "retrieve_from_professor_corpus"
    # Receipts harvested from the retrieval tool result.
    assert any(r.source_title == "Attention Paper" for r in advocate_turn.receipts)


@pytest.mark.asyncio
async def test_baseline_retrieval_query_built_from_profile_and_claims() -> None:
    retriever = FakeRetriever()
    models = {
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling()),
    }
    outreach = _outreach()
    await _engine(models, retriever=retriever).run(outreach, _professor(outreach.professor_id))

    assert len(retriever.searched_queries) == 1
    assert "AI safety" in retriever.searched_queries[0]
    assert "NeurIPS" in retriever.searched_queries[0]


@pytest.mark.asyncio
async def test_arbitrator_closing_turn_appended_with_rationale() -> None:
    models = {
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel([], ruling=_ruling("decline")),
    }
    outreach = _outreach()
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    closing = outcome.trace.turns[-1]
    assert closing.role == AgentRole.ARBITRATOR
    assert closing.content == "Strong fit per [REF:0]."
    assert closing.references_turn_ids == [0]
    assert outcome.decision.label == "decline"
