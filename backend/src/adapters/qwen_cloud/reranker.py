from __future__ import annotations

import httpx

from src.adapters.qwen_cloud.compliance import assert_qwen_host
from src.application.ports.outbound.reranker import Reranker, RerankResult
from src.config import get_settings
from src.domain.exceptions.base import ExternalToolError


class QwenReranker(Reranker):
    """qwen3-rerank via DashScope's Model Studio workspace-scoped host.

    Unlike chat/embeddings, reranking lives on a per-workspace subdomain
    (`{workspace_id}.{region}.maas.aliyuncs.com`), not `DASHSCOPE_BASE_URL`.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.DASHSCOPE_API_KEY
        self._model = settings.DASHSCOPE_RERANK_MODEL
        self._timeout = settings.DASHSCOPE_TIMEOUT
        self._url = (
            f"https://{settings.DASHSCOPE_WORKSPACE_ID}."
            f"{settings.DASHSCOPE_RERANK_REGION}.maas.aliyuncs.com"
            f"/compatible-mode/v1/reranks"
        )
        assert_qwen_host(self._url)

    async def rerank(
        self, query: str, documents: list[str], top_n: int | None = None
    ) -> list[RerankResult]:
        if not documents:
            return []
        if not self._api_key:
            raise ExternalToolError("DASHSCOPE_API_KEY is not configured")
        if not get_settings().DASHSCOPE_WORKSPACE_ID:
            raise ExternalToolError("DASHSCOPE_WORKSPACE_ID is not configured")

        payload: dict = {"model": self._model, "query": query, "documents": documents}
        if top_n is not None:
            payload["top_n"] = top_n

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
            for r in data["results"]
        ]
