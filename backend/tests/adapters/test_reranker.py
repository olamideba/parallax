from __future__ import annotations

import json

import httpx
import pytest

from src.adapters.qwen_cloud.reranker import QwenReranker
from src.config import get_settings
from src.domain.exceptions.base import ExternalToolError


def _patch_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    transport = httpx.MockTransport(handler)

    class _PatchedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _PatchedAsyncClient)


@pytest.fixture(autouse=True)
def _configure_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-key")
    monkeypatch.setenv("DASHSCOPE_WORKSPACE_ID", "ws-test123")
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_rerank_hits_native_endpoint_and_parses_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "output": {
                    "results": [
                        {"index": 1, "relevance_score": 0.93},
                        {"index": 0, "relevance_score": 0.41},
                    ]
                }
            },
        )

    _patch_client(monkeypatch, handler)

    reranker = QwenReranker()
    results = await reranker.rerank("AI safety", ["doc a", "doc b"], top_n=2)

    # Native DashScope rerank service on the same host as chat/embeddings —
    # NOT the workspace subdomain (which 404s).
    assert captured["url"] == (
        "https://dashscope-intl.aliyuncs.com"
        "/api/v1/services/rerank/text-rerank/text-rerank"
    )
    assert captured["body"]["input"] == {"query": "AI safety", "documents": ["doc a", "doc b"]}
    assert captured["body"]["parameters"]["top_n"] == 2
    assert [r.index for r in results] == [1, 0]
    assert results[0].relevance_score == 0.93


@pytest.mark.asyncio
async def test_rerank_returns_empty_for_no_documents() -> None:
    reranker = QwenReranker()
    assert await reranker.rerank("query", []) == []


@pytest.mark.asyncio
async def test_rerank_without_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")
    get_settings.cache_clear()
    reranker = QwenReranker()
    with pytest.raises(ExternalToolError, match="DASHSCOPE_API_KEY"):
        await reranker.rerank("query", ["doc"])
