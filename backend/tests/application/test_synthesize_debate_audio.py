from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.application.ports.outbound.tts_client import SynthesizedSpeech
from src.application.use_cases.synthesize_debate_audio import (
    SynthesizeDebateAudioUseCase,
)
from src.domain.exceptions.base import ExternalToolError
from src.domain.models.society import AgentRole, DebateTrace, DebateTurn


def _turn(role: AgentRole, content: str) -> DebateTurn:
    return DebateTurn(round=1, role=role, content=content, created_at=datetime.now(UTC))


def _trace(turns: list[DebateTurn]) -> DebateTrace:
    return DebateTrace(
        id=uuid4(),
        outreach_id=uuid4(),
        professor_id=uuid4(),
        turns=turns,
        round_cap=3,
        started_at=datetime.now(UTC),
    )


class FakeTraceRepo:
    def __init__(self, trace: DebateTrace | None) -> None:
        self._trace = trace
        self.saved: DebateTrace | None = None

    async def get_by_outreach_id(self, outreach_id):  # noqa: ANN001
        return self._trace

    async def save(self, trace):  # noqa: ANN001
        self.saved = trace
        return trace


class FakeProfessorRepo:
    def __init__(self, professor=None) -> None:  # noqa: ANN001
        self._professor = professor

    async def get_by_id(self, professor_id):  # noqa: ANN001
        return self._professor


class FakeSpokenLineWriter:
    def __init__(self) -> None:
        self.professor_names: list[str | None] = []

    async def to_spoken_line(self, role, content, professor_name=None):  # noqa: ANN001
        self.professor_names.append(professor_name)
        return f"spoken:{content[:10]}"


class FakeTts:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def synthesize(self, text, voice):  # noqa: ANN001
        self.calls.append((text, voice))
        return SynthesizedSpeech(audio=b"MP3", duration_ms=4200)


class FakeStorage:
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}

    async def upload(self, storage_key, data, content_type="application/pdf"):  # noqa: ANN001
        self.uploaded[storage_key] = data
        return storage_key

    async def download(self, storage_key):  # noqa: ANN001
        return self.uploaded[storage_key]


@pytest.mark.asyncio
async def test_synthesizes_audio_for_each_turn() -> None:
    trace = _trace([_turn(AgentRole.ADVOCATE, "long content one"),
                    _turn(AgentRole.AUDITOR, "long content two")])
    repo = FakeTraceRepo(trace)
    tts = FakeTts()
    storage = FakeStorage()
    use_case = SynthesizeDebateAudioUseCase(
        trace_repo=repo,
        professor_repo=FakeProfessorRepo(),
        spoken_line_writer=FakeSpokenLineWriter(),
        tts_client=tts,
        object_storage=storage,
    )

    count = await use_case.execute(trace.outreach_id)

    assert count == 2
    assert len(tts.calls) == 2
    saved = repo.saved
    assert saved is not None
    for i, turn in enumerate(saved.turns):
        assert turn.spoken_line is not None
        assert turn.audio_key == f"debates/{trace.id}/turns/{i}.wav"
        assert turn.audio_duration_ms == 4200
        assert turn.audio_key in storage.uploaded
    # Each turn is voiced by its persona's distinct Qwen3-TTS voice.
    assert tts.calls[0][1] != tts.calls[1][1]


@pytest.mark.asyncio
async def test_professor_name_threaded_to_spoken_line() -> None:
    trace = _trace([_turn(AgentRole.ADVOCATE, "content")])
    professor = SimpleNamespace(display_name="Dr. Olamide Olamide")
    writer = FakeSpokenLineWriter()
    use_case = SynthesizeDebateAudioUseCase(
        trace_repo=FakeTraceRepo(trace),
        professor_repo=FakeProfessorRepo(professor),
        spoken_line_writer=writer,
        tts_client=FakeTts(),
        object_storage=FakeStorage(),
    )

    await use_case.execute(trace.outreach_id)

    assert writer.professor_names == ["Dr. Olamide Olamide"]


@pytest.mark.asyncio
async def test_missing_trace_is_noop() -> None:
    repo = FakeTraceRepo(None)
    use_case = SynthesizeDebateAudioUseCase(
        trace_repo=repo,
        professor_repo=FakeProfessorRepo(),
        spoken_line_writer=FakeSpokenLineWriter(),
        tts_client=FakeTts(),
        object_storage=FakeStorage(),
    )

    count = await use_case.execute(uuid4())

    assert count == 0
    assert repo.saved is None


@pytest.mark.asyncio
async def test_per_turn_failure_degrades_silently() -> None:
    trace = _trace([_turn(AgentRole.ADVOCATE, "content a"),
                    _turn(AgentRole.AUDITOR, "content b")])
    repo = FakeTraceRepo(trace)

    class HalfBrokenTts(FakeTts):
        async def synthesize(self, text, voice):  # noqa: ANN001
            if "content a" in text:
                raise ExternalToolError("TTS down")
            return await super().synthesize(text, voice)

    use_case = SynthesizeDebateAudioUseCase(
        trace_repo=repo,
        professor_repo=FakeProfessorRepo(),
        spoken_line_writer=FakeSpokenLineWriter(),
        tts_client=HalfBrokenTts(),
        object_storage=FakeStorage(),
    )

    count = await use_case.execute(trace.outreach_id)

    # The healthy turn still gets audio; the failed one degrades to null,
    # and the trace is still saved (partial audio, playback falls back).
    assert count == 1
    saved = repo.saved
    assert saved is not None
    assert saved.turns[0].audio_key is None
    assert saved.turns[1].audio_key is not None


@pytest.mark.asyncio
async def test_already_synthesized_turns_are_skipped() -> None:
    done = _turn(AgentRole.ADVOCATE, "already done")
    done.audio_key = "debates/x/turns/0.wav"
    trace = _trace([done, _turn(AgentRole.AUDITOR, "needs audio")])
    repo = FakeTraceRepo(trace)
    tts = FakeTts()
    use_case = SynthesizeDebateAudioUseCase(
        trace_repo=repo,
        professor_repo=FakeProfessorRepo(),
        spoken_line_writer=FakeSpokenLineWriter(),
        tts_client=tts,
        object_storage=FakeStorage(),
    )

    count = await use_case.execute(trace.outreach_id)

    assert count == 1
    assert len(tts.calls) == 1  # only the un-synthesized turn hit TTS


@pytest.mark.asyncio
async def test_force_resynthesizes_already_done_turns() -> None:
    done = _turn(AgentRole.ADVOCATE, "already done")
    done.audio_key = "debates/x/turns/0.wav"
    done.audio_duration_ms = 999
    trace = _trace([done, _turn(AgentRole.AUDITOR, "needs audio")])
    repo = FakeTraceRepo(trace)
    tts = FakeTts()
    use_case = SynthesizeDebateAudioUseCase(
        trace_repo=repo,
        professor_repo=FakeProfessorRepo(),
        spoken_line_writer=FakeSpokenLineWriter(),
        tts_client=tts,
        object_storage=FakeStorage(),
    )

    count = await use_case.execute(trace.outreach_id, force=True)

    assert count == 2
    assert len(tts.calls) == 2  # both turns re-synthesized
    saved = repo.saved
    assert saved is not None
    assert saved.turns[0].audio_duration_ms == 4200  # overwritten, not left stale
