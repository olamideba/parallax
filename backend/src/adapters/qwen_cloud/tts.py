from __future__ import annotations

import struct
from urllib.parse import urlparse

import dashscope
import httpx

from src.adapters.qwen_cloud.compliance import assert_qwen_host
from src.application.ports.outbound.tts_client import (
    SynthesizedSpeech,
    TextToSpeechClient,
)
from src.config import get_settings
from src.domain.exceptions.base import ExternalToolError

# Qwen3-TTS is served over plain HTTP via MultiModalConversation.call (not the
# WebSocket-only CosyVoice tts_v2 client — that's a different model family and
# rejects these model ids with ModelNotFound). The call returns a short-lived
# URL to a WAV file, which we then download. dashscope.base_http_api_url must
# be pinned explicitly to the Qwen-Cloud host or the SDK falls back to the
# domestic endpoint and an international key 401s there.
_WAV_HEADER_SIZE = 44


class QwenTtsClient(TextToSpeechClient):
    """DashScope Qwen3-TTS text-to-speech (satisfies the Qwen-Cloud-only rule).

    Rides on the same DASHSCOPE_API_KEY as chat/embeddings. Returns WAV bytes
    plus the exact duration (derived from the real byte rate — the WAV header's
    declared size is a placeholder and cannot be trusted) so the replay clock
    can be driven by real audio length instead of a character-count heuristic.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.DASHSCOPE_API_KEY
        self._model = settings.DASHSCOPE_TTS_MODEL
        parsed = urlparse(settings.DASHSCOPE_BASE_URL)
        self._http_url = f"{parsed.scheme}://{parsed.netloc}/api/v1"
        self._timeout = settings.DASHSCOPE_TTS_TIMEOUT
        assert_qwen_host(self._http_url)

    async def synthesize(self, text: str, voice: str) -> SynthesizedSpeech:
        if not self._api_key:
            raise ExternalToolError("DASHSCOPE_API_KEY is not configured")
        if not text.strip():
            raise ExternalToolError("Cannot synthesize empty text")

        dashscope.api_key = self._api_key
        dashscope.base_http_api_url = self._http_url
        response = dashscope.MultiModalConversation.call(
            model=self._model,
            text=text,
            voice=voice,
            language_type="English",
            stream=False,
        )
        if response.status_code != 200 or response.output is None:
            raise ExternalToolError(
                f"Qwen3-TTS synthesis failed ({response.status_code}): {response.message}"
            )

        audio_url = response.output.audio.url
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            audio = audio_resp.content

        if not audio:
            raise ExternalToolError("Qwen3-TTS returned no audio")
        return SynthesizedSpeech(
            audio=audio, duration_ms=_duration_ms(audio), content_type="audio/wav"
        )


def _duration_ms(wav: bytes) -> int:
    # The RIFF/data chunk sizes in the response header are placeholder max
    # values, not the real size — compute duration from the actual downloaded
    # byte count and the header's (trustworthy) byte rate instead.
    byte_rate = struct.unpack("<I", wav[28:32])[0]
    data_bytes = max(0, len(wav) - _WAV_HEADER_SIZE)
    if byte_rate <= 0:
        return 1
    return max(1, round(data_bytes / byte_rate * 1000))
