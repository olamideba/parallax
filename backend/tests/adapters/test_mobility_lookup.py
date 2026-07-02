from __future__ import annotations

import httpx
import pytest

from src.adapters.mcp.tools.mobility_lookup import lookup_student_mobility, mobility_lookup_tool
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
def _configure(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-key")
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_lookup_sends_enable_search_and_returns_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Visas typically required..."}}]},
        )

    _patch_client(monkeypatch, handler)

    result = await lookup_student_mobility("Nigeria", "United States")

    assert captured["body"]["enable_search"] is True
    assert "Nigeria" in captured["body"]["messages"][0]["content"]
    assert result["summary"] == "Visas typically required..."
    assert result["country"] == "Nigeria"
    assert "time-sensitive" in result["note"]


@pytest.mark.asyncio
async def test_lookup_without_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(ExternalToolError, match="DASHSCOPE_API_KEY"):
        await lookup_student_mobility("Nigeria", "United States")


@pytest.mark.asyncio
async def test_mobility_lookup_tool_is_invokable(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "summary text"}}]}
        )

    _patch_client(monkeypatch, handler)

    result = await mobility_lookup_tool.ainvoke(
        {"country": "Nigeria", "destination_country": "Canada"}
    )

    assert result["summary"] == "summary text"
    assert result["destination_country"] == "Canada"
