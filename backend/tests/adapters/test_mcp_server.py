from __future__ import annotations

import pytest

from src.adapters.mcp import server as server_module
from src.adapters.mcp.server import LocalMcpToolBus


@pytest.mark.asyncio
async def test_list_tools_advertises_mobility_lookup() -> None:
    bus = LocalMcpToolBus()
    tools = await bus.list_tools()
    names = {t["name"] for t in tools}
    assert "lookup_student_mobility" in names


@pytest.mark.asyncio
async def test_call_tool_dispatches_to_mobility_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_lookup(country: str, destination_country: str) -> dict:
        return {"country": country, "destination_country": destination_country, "summary": "ok"}

    monkeypatch.setattr(server_module, "lookup_student_mobility", fake_lookup)

    bus = LocalMcpToolBus()
    result = await bus.call_tool(
        "lookup_student_mobility", {"country": "Nigeria", "destination_country": "Canada"}
    )

    assert result["summary"] == "ok"
    assert result["destination_country"] == "Canada"


@pytest.mark.asyncio
async def test_call_unknown_tool_raises() -> None:
    bus = LocalMcpToolBus()
    with pytest.raises(ValueError, match="Unknown tool"):
        await bus.call_tool("does-not-exist", {})
