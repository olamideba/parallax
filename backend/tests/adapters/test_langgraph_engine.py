from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from src.adapters.orchestration.langgraph_engine import (
    ArbitratorRuling,
    LangGraphNegotiationEngine,
    _ModeratorChoice,
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
    """Serves a structured-output value: a single object, or a list popped per
    call (used to script the Moderator's per-turn routing choices)."""

    def __init__(self, value) -> None:  # noqa: ANN001
        self._value = value
        self.last_prompt: str | None = None

    async def ainvoke(self, prompt):  # noqa: ANN001
        self.last_prompt = prompt
        if isinstance(self._value, list):
            return self._value.pop(0)
        return self._value


class FakeChatModel:
    """Pops one scripted response per ainvoke call; bind_tools is a no-op.

    `structured` backs `with_structured_output` — an ArbitratorRuling for the
    Arbitrator model, or a list of _ModeratorChoice for the Moderator model.
    """

    def __init__(self, responses: list | None = None, structured=None) -> None:  # noqa: ANN001
        self._responses = responses or []
        self._structured = FakeStructured(
            structured
            if structured is not None
            else ArbitratorRuling(
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


def _moderator(*picks: str) -> FakeChatModel:
    """A Moderator that routes the floor to `picks` in order (each a role value
    or "end"). The engine's hard caps backstop it once the picks run out."""
    return FakeChatModel(
        structured=[_ModeratorChoice(next_speaker=p, reason="test") for p in picks]
    )


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
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "end"),
        AgentRole.ADVOCATE: FakeChatModel(["Alignment is real.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["Claim 1: VERIFIED — ok.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["One slot open.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling("invite")),
    }
    outreach = _outreach()
    outcome = await _engine(models, round_cap=3).run(outreach, _professor(outreach.professor_id))

    roles = [t.role for t in outcome.trace.turns]
    assert roles.count(AgentRole.ARBITRATOR) == 1
    # Each debater is heard once, then the Moderator ends the debate.
    debater_turns = [t for t in outcome.trace.turns if t.role != AgentRole.ARBITRATOR]
    assert len(debater_turns) == 3
    assert all(t.round == 1 for t in debater_turns)
    assert outcome.trace.terminated_at_round == 1
    assert outcome.decision.label == "invite"
    assert outcome.decision.drafted_reply == "Dear Jon, ..."


@pytest.mark.asyncio
async def test_hard_turn_cap_terminates_persistent_disagreement() -> None:
    talk = ["arguing"] * 10  # never passes
    # The Moderator keeps routing the floor; the engine's hard cap
    # (round_cap * debaters = 6) forces termination regardless.
    models = {
        AgentRole.GATEKEEPER: _moderator(
            "advocate", "auditor", "assessor", "advocate", "auditor", "assessor"
        ),
        AgentRole.ADVOCATE: FakeChatModel(list(talk)),
        AgentRole.AUDITOR: FakeChatModel(list(talk)),
        AgentRole.ASSESSOR: FakeChatModel(list(talk)),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling("request_more_info")),
    }
    outreach = _outreach()
    outcome = await _engine(models, round_cap=2).run(outreach, _professor(outreach.professor_id))

    debater_turns = [t for t in outcome.trace.turns if t.role != AgentRole.ARBITRATOR]
    assert len(debater_turns) == 6  # hard cap = round_cap(2) * debaters(3)
    assert outcome.trace.terminated_at_round == 2
    assert outcome.trace.round_cap == 2


@pytest.mark.asyncio
async def test_receipts_and_references_are_parsed_from_content() -> None:
    advocate_text = (
        'Fit is genuine [RECEIPT: "Attention Paper", "the exact excerpt"]. See [REF:0].'
    )
    models = {
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "end"),
        AgentRole.ADVOCATE: FakeChatModel([advocate_text, "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["capacity fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
    }
    outreach = _outreach()
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    advocate_turn = next(t for t in outcome.trace.turns if t.role == AgentRole.ADVOCATE)
    assert advocate_turn.receipts[0].source_title == "Attention Paper"
    assert advocate_turn.receipts[0].chunk_text == "the exact excerpt"
    # The Advocate opens, so its turn has no prior turns — REF:0 is out of range
    # and dropped.
    assert advocate_turn.references_turn_ids == []


@pytest.mark.asyncio
async def test_later_turn_references_resolve_against_transcript() -> None:
    # Advocate opens (idx 0), Auditor (idx 1), Assessor (idx 2), then the
    # Moderator hands the Advocate the floor again to rebut turn 1.
    models = {
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "advocate", "end"),
        AgentRole.ADVOCATE: FakeChatModel(["opening case.", "Rebutting [REF:1]."]),
        AgentRole.AUDITOR: FakeChatModel(["opening audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["opening assessment.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
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
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "end"),
        AgentRole.ADVOCATE: FakeChatModel([tool_call_msg, "Found strong overlap.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
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
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "end"),
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
    }
    outreach = _outreach()
    await _engine(models, retriever=retriever).run(outreach, _professor(outreach.professor_id))

    assert len(retriever.searched_queries) == 1
    assert "AI safety" in retriever.searched_queries[0]
    assert "NeurIPS" in retriever.searched_queries[0]


@pytest.mark.asyncio
async def test_gatekeeper_opening_seeds_transcript_when_reason_present() -> None:
    # The Gatekeeper model serves two roles: a plain opening statement, then the
    # structured Moderator routing for the rest of the debate.
    models = {
        AgentRole.GATEKEEPER: FakeChatModel(
            responses=["I let this one through — the RAG work is a real thread."],
            structured=[
                _ModeratorChoice(next_speaker=p, reason="test")
                for p in ("advocate", "auditor", "assessor", "end")
            ],
        ),
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
    }
    outreach = _outreach()
    outreach.triage_reason = "Plausible alignment with the professor's RAG work."
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    first = outcome.trace.turns[0]
    assert first.role == AgentRole.GATEKEEPER
    assert first.round == 1
    assert "thread" in first.content
    # The debaters follow the Gatekeeper's opening.
    assert outcome.trace.turns[1].role == AgentRole.ADVOCATE


@pytest.mark.asyncio
async def test_no_gatekeeper_opening_when_reason_absent() -> None:
    models = {
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "end"),
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
    }
    outreach = _outreach()  # triage_reason defaults to None
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    assert outcome.trace.turns[0].role == AgentRole.ADVOCATE
    assert all(t.role != AgentRole.GATEKEEPER for t in outcome.trace.turns)


@pytest.mark.asyncio
async def test_continues_marker_gives_same_speaker_the_next_turn() -> None:
    # The Moderator only ever picks "auditor" once — the second and third
    # Auditor turns happen purely because [CONTINUES] force-routes the floor
    # back, with no Moderator involvement (and no extra scripted pick needed).
    models = {
        AgentRole.GATEKEEPER: _moderator("auditor", "advocate", "assessor", "end"),
        AgentRole.AUDITOR: FakeChatModel(
            [
                "Claim 1: VERIFIED — ok. [CONTINUES]",
                "Claim 2: DISPUTED — no. [CONTINUES]",
                "Claim 3: fine.",
                "PASS",
            ]
        ),
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
    }
    outreach = _outreach()
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    auditor_turns = [t for t in outcome.trace.turns if t.role == AgentRole.AUDITOR]
    assert len(auditor_turns) == 3
    assert auditor_turns[0].content == "Claim 1: VERIFIED — ok."
    assert auditor_turns[1].content == "Claim 2: DISPUTED — no."
    assert auditor_turns[2].content == "Claim 3: fine."
    # The [CONTINUES] marker is stripped and never leaks into stored content.
    assert all("CONTINUES" not in t.content for t in auditor_turns)
    # All three stay in the same round — a continuation is not a loop-back.
    assert len({t.round for t in auditor_turns}) == 1


@pytest.mark.asyncio
async def test_continuation_streak_is_capped_regardless_of_marker() -> None:
    from src.config import get_settings

    cap = get_settings().DEBATE_MAX_CONTINUATIONS
    # The Auditor claims [CONTINUES] forever — the hard per-speaker cap must
    # still force it to stop after `cap` consecutive turns, handing the floor
    # back to the Moderator instead of monopolizing the debate.
    endless = [f"Point {i}. [CONTINUES]" for i in range(cap + 3)]
    models = {
        AgentRole.GATEKEEPER: _moderator("auditor", "end"),
        AgentRole.AUDITOR: FakeChatModel(list(endless)),
        AgentRole.ADVOCATE: FakeChatModel(["PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling()),
    }
    outreach = _outreach()
    outcome = await _engine(models, round_cap=5).run(outreach, _professor(outreach.professor_id))

    auditor_turns = [t for t in outcome.trace.turns if t.role == AgentRole.AUDITOR]
    assert len(auditor_turns) == cap


@pytest.mark.asyncio
async def test_arbitrator_closing_turn_appended_with_rationale() -> None:
    models = {
        AgentRole.GATEKEEPER: _moderator("advocate", "auditor", "assessor", "end"),
        AgentRole.ADVOCATE: FakeChatModel(["case.", "PASS"]),
        AgentRole.AUDITOR: FakeChatModel(["audit.", "PASS"]),
        AgentRole.ASSESSOR: FakeChatModel(["fine.", "PASS"]),
        AgentRole.ARBITRATOR: FakeChatModel(structured=_ruling("decline")),
    }
    outreach = _outreach()
    outcome = await _engine(models).run(outreach, _professor(outreach.professor_id))

    closing = outcome.trace.turns[-1]
    assert closing.role == AgentRole.ARBITRATOR
    assert closing.content == "Strong fit per [REF:0]."
    assert closing.references_turn_ids == [0]
    assert outcome.decision.label == "decline"
