from __future__ import annotations

from urllib.parse import urlparse

import httpx

from src.adapters.qwen_cloud.compliance import assert_qwen_host
from src.application.ports.outbound.reranker import Reranker, RerankResult
from src.config import get_settings
from src.domain.exceptions.base import ExternalToolError

# qwen3-rerank is served by DashScope's native (DashScope-format) API, not the
# OpenAI-compatible surface: POST /api/v1/services/rerank/text-rerank/text-rerank
# on the same host as chat/embeddings. The `{workspace}.maas.aliyuncs.com`
# subdomain + `/compatible-mode/v1/reranks` path 404s — it does not exist.
_RERANK_PATH = "/api/v1/services/rerank/text-rerank/text-rerank"


class QwenReranker(Reranker):
    """qwen3-rerank via DashScope's native rerank service.

    Rides on the same host + key as chat/embeddings (`DASHSCOPE_BASE_URL`); the
    workspace is carried by the `sk-ws-*` key itself, so no subdomain is needed.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.DASHSCOPE_API_KEY
        self._model = settings.DASHSCOPE_RERANK_MODEL
        self._timeout = settings.DASHSCOPE_TIMEOUT
        parsed = urlparse(settings.DASHSCOPE_BASE_URL)
        self._url = f"{parsed.scheme}://{parsed.netloc}{_RERANK_PATH}"
        assert_qwen_host(self._url)

    async def rerank(
        self, query: str, documents: list[str], top_n: int | None = None
    ) -> list[RerankResult]:
        if not documents:
            return []
        if not self._api_key:
            raise ExternalToolError("DASHSCOPE_API_KEY is not configured")

        parameters: dict = {"return_documents": False}
        if top_n is not None:
            parameters["top_n"] = top_n
        payload = {
            "model": self._model,
            "input": {"query": query, "documents": documents},
            "parameters": parameters,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                self._url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        return [
            RerankResult(index=r["index"], relevance_score=r["relevance_score"])
            for r in data["output"]["results"]
        ]
