from __future__ import annotations

from uuid import UUID

from loguru import logger

from src.adapters.qwen_cloud.personas import persona_for
from src.application.ports.outbound.object_storage import ObjectStorage
from src.application.ports.outbound.repository import DebateTraceRepository
from src.application.ports.outbound.spoken_line_writer import SpokenLineWriter
from src.application.ports.outbound.tts_client import TextToSpeechClient
from src.domain.models.society import DebateTrace, DebateTurn


class SynthesizeDebateAudioUseCase:
    """Post-debate step: give every turn a short spoken line and synthesized
    audio for the replay. Runs after `run_debate` has saved the trace, off the
    debate's critical path — the debate's correctness never depends on it.

    Each turn is handled independently and best-effort: a turn whose synthesis
    fails keeps `audio_key=None`, and the replay silently falls back to a
    heuristic-duration silent beat for it rather than breaking playback.
    """

    def __init__(
        self,
        trace_repo: DebateTraceRepository,
        spoken_line_writer: SpokenLineWriter,
        tts_client: TextToSpeechClient,
        object_storage: ObjectStorage,
    ) -> None:
        self._trace_repo = trace_repo
        self._spoken_line_writer = spoken_line_writer
        self._tts = tts_client
        self._storage = object_storage

    async def execute(self, outreach_id: UUID, force: bool = False) -> int:
        trace = await self._trace_repo.get_by_outreach_id(outreach_id)
        if trace is None:
            logger.warning("Audio: no trace for outreach {}", outreach_id)
            return 0

        synthesized = 0
        for index, turn in enumerate(trace.turns):
            if turn.audio_key is not None and not force:
                # Idempotent re-run — leave already-synthesized turns alone.
                continue
            if await self._synthesize_turn(trace, index, turn):
                synthesized += 1

        await self._trace_repo.save(trace)
        logger.info(
            "Audio synthesized for {}/{} turns of outreach {}",
            synthesized,
            len(trace.turns),
            outreach_id,
        )
        return synthesized

    async def _synthesize_turn(
        self, trace: DebateTrace, index: int, turn: DebateTurn
    ) -> bool:
        try:
            spoken_line = await self._spoken_line_writer.to_spoken_line(
                turn.role, turn.content
            )
            if not spoken_line:
                return False
            voice = persona_for(turn.role).voice_id
            speech = await self._tts.synthesize(spoken_line, voice)
            key = f"debates/{trace.id}/turns/{index}.mp3"
            await self._storage.upload(key, speech.audio, content_type=speech.content_type)
        except Exception:  # noqa: BLE001 — one turn's failure must not sink the rest
            logger.exception(
                "Audio synthesis failed for turn {} of outreach {}",
                index,
                trace.outreach_id,
            )
            return False

        turn.spoken_line = spoken_line
        turn.audio_key = key
        turn.audio_duration_ms = speech.duration_ms
        return True
