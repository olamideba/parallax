from __future__ import annotations

from src.application.ports.outbound.llm_client import LLMClient
from src.config import get_settings


class QwenLLMClient(LLMClient):
    """DashScope-backed LLM client for Qwen models."""

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self._default_model = model or settings.QWEN_MODEL_DEBATE
        self._api_key = settings.DASHSCOPE_API_KEY

    async def complete(self, messages: list[dict], model: str | None = None) -> str:
        raise NotImplementedError

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError
