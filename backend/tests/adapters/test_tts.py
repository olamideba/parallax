from __future__ import annotations

import struct
from types import SimpleNamespace

import httpx
import pytest

import src.adapters.qwen_cloud.tts as tts_module
from src.adapters.qwen_cloud.tts import QwenTtsClient
from src.config import get_settings
from src.domain.exceptions.base import ExternalToolError


@pytest.fixture(autouse=True)
def _configure_key(monkeypatch: pytest.MonkeyPatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-key")
    yield
    get_settings.cache_clear()


def _wav_header(byte_rate: int) -> bytes:
    # Minimal 44-byte RIFF/WAV header; only byte-rate (offset 28) is read by
    # the adapter, the rest just needs to be structurally present.
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 0, b"WAVE", b"fmt ", 16, 1, 1, 24000, byte_rate, 2, 16, b"data", 0,
    )


class _FakeCall:
    def __init__(self, status_code=200, audio_url="https://example.com/a.wav", message="OK"):
        self.status_code = status_code
        self.message = message
        self.output = (
            SimpleNamespace(audio=SimpleNamespace(url=audio_url))
            if status_code == 200
            else None
        )
        self.captured: dict = {}

    def __call__(self, **kwargs):
        self.captured = kwargs
        return self


def _patch_download(monkeypatch: pytest.MonkeyPatch, audio_bytes: bytes) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=audio_bytes)

    transport = httpx.MockTransport(handler)

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _PatchedAsyncClient)


@pytest.mark.asyncio
async def test_synthesize_passes_voice_and_returns_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio = _wav_header(byte_rate=48000) + b"\x00" * 48000  # 1 second of PCM
    fake_call = _FakeCall()
    monkeypatch.setattr(tts_module.dashscope.MultiModalConversation, "call", fake_call)
    _patch_download(monkeypatch, audio)

    speech = await QwenTtsClient().synthesize("Hello there.", "Cherry")

    assert speech.audio == audio
    assert speech.duration_ms == 1000
    assert speech.content_type == "audio/wav"
    assert fake_call.captured["voice"] == "Cherry"
    assert fake_call.captured["model"] == "qwen3-tts-flash"
    assert fake_call.captured["text"] == "Hello there."


@pytest.mark.asyncio
async def test_empty_text_rejected() -> None:
    with pytest.raises(ExternalToolError):
        await QwenTtsClient().synthesize("   ", "Cherry")


@pytest.mark.asyncio
async def test_non_200_response_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_call = _FakeCall(status_code=401, message="Invalid API-key provided.")
    monkeypatch.setattr(tts_module.dashscope.MultiModalConversation, "call", fake_call)

    with pytest.raises(ExternalToolError, match="401"):
        await QwenTtsClient().synthesize("hi", "Cherry")


@pytest.mark.asyncio
async def test_empty_downloaded_audio_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_call = _FakeCall()
    monkeypatch.setattr(tts_module.dashscope.MultiModalConversation, "call", fake_call)
    _patch_download(monkeypatch, b"")

    with pytest.raises(ExternalToolError, match="no audio"):
        await QwenTtsClient().synthesize("hi", "Cherry")


def test_rejects_non_qwen_host(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://evil.example.com/compatible-mode/v1")
    with pytest.raises(ValueError, match="non-Qwen host"):
        QwenTtsClient()
    get_settings.cache_clear()
