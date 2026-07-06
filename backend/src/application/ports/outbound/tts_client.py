from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class SynthesizedSpeech(BaseModel):
    audio: bytes
    duration_ms: int
    content_type: str = "audio/mpeg"


class TextToSpeechClient(ABC):
    """Turns a line of text into speech audio (mirrors LLMClient).

    Implementations live in adapters; per the hackathon constraint the concrete
    adapter must route through Qwen Cloud managed APIs (DashScope Qwen3-TTS) on
    the same key as the model calls.
    """

    @abstractmethod
    async def synthesize(self, text: str, voice: str) -> SynthesizedSpeech:
        raise NotImplementedError
