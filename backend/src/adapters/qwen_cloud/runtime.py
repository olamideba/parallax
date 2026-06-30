from __future__ import annotations

import httpx

from src.application.ports.outbound.llm_client import LLMClient
from src.config import get_settings
from src.domain.exceptions.base import IngestionError


class QwenLLMClient(LLMClient):
    """DashScope-backed LLM client for Qwen models."""

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self._default_model = model or settings.QWEN_MODEL_DEBATE
        self._api_key = settings.DASHSCOPE_API_KEY
        self._base_url = settings.DASHSCOPE_BASE_URL
        self._embed_model = settings.DASHSCOPE_EMBED_MODEL
        self._embed_dims = settings.DASHSCOPE_EMBED_DIMS
        self._timeout = settings.DASHSCOPE_TIMEOUT

    async def complete(self, messages: list[dict], model: str | None = None) -> str:
        raise NotImplementedError

    async def embed(self, text: str) -> list[float]:
        if not self._api_key:
            raise IngestionError("DASHSCOPE_API_KEY is not configured")
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._embed_model,
                    "input": text,
                    "dimensions": self._embed_dims,
                    "encoding_format": "float",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return data["data"][0]["embedding"]
