from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class RerankResult(BaseModel):
    index: int  # position in the original `documents` list passed to rerank()
    relevance_score: float


class Reranker(ABC):
    """Second-pass relevance sort over an initial retrieval candidate set."""

    @abstractmethod
    async def rerank(
        self, query: str, documents: list[str], top_n: int | None = None
    ) -> list[RerankResult]:
        raise NotImplementedError
