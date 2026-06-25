from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class McpToolBus(ABC):
    @abstractmethod
    async def list_tools(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        raise NotImplementedError
