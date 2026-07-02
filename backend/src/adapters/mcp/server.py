from __future__ import annotations

from typing import Any

from src.adapters.mcp.tools.mobility_lookup import lookup_student_mobility
from src.application.ports.outbound.mcp_tool_bus import McpToolBus

_TOOL_SCHEMAS: list[dict] = [
    {
        "name": "lookup_student_mobility",
        "description": (
            "Live web-search-grounded lookup for student-visa/mobility "
            "considerations between two countries. Use when assessing whether "
            "an international candidate's visa/mobility situation is a genuine "
            "feasibility concern — never assume this from memory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "country": {
                    "type": "string",
                    "description": "Candidate's country of citizenship.",
                },
                "destination_country": {
                    "type": "string",
                    "description": "Country where the professor's institution is located.",
                },
            },
            "required": ["country", "destination_country"],
        },
    },
]


class LocalMcpToolBus(McpToolBus):
    """Runs MCP-classified tools in-process (no remote MCP server required for
    local dev/demo). Currently exposes one genuinely external tool: a live,
    web-search-grounded student mobility/visa lookup (ActionKind.MCP)."""

    async def list_tools(self) -> list[dict]:
        return _TOOL_SCHEMAS

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "lookup_student_mobility":
            return await lookup_student_mobility(**arguments)
        raise ValueError(f"Unknown tool: {name!r}")
