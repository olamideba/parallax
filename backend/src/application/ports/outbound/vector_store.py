from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, doc_id: UUID, text: str, embedding: list[float], metadata: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    async def query(
        self,
        embedding: list[float],
        professor_id: UUID,
        top_k: int = 5,
    ) -> list[dict]:
        raise NotImplementedError
