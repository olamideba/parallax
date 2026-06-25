from __future__ import annotations

from typing import Any

from src.application.ports.outbound.mcp_tool_bus import McpToolBus


class LocalMcpToolBus(McpToolBus):
    """Runs MCP tools in-process (no remote server required for local dev)."""

    async def list_tools(self) -> list[dict]:
        raise NotImplementedError

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        raise NotImplementedError
