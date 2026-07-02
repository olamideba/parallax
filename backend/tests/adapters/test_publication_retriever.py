from __future__ import annotations

from uuid import uuid4

import pytest

from src.adapters.mcp.tools.publication_retriever import PublicationRetriever
from src.application.ports.outbound.reranker import RerankResult
from src.domain.models.professor import Publication, PublicationStatus


class FakeLLMClient:
    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    async def complete(self, messages, model=None):  # pragma: no cover - unused
        raise NotImplementedError


class FakeVectorStore:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.last_query_args: tuple | None = None

    async def upsert(self, doc_id, text, embedding, metadata):  # pragma: no cover - unused
        raise NotImplementedError

    async def query(self, embedding, professor_id, top_k=5):
        self.last_query_args = (embedding, professor_id, top_k)
        return self._rows[:top_k]


class FakePublicationRepo:
    def __init__(self, titles: dict[str, str]) -> None:
        self._titles = titles

    async def get(self, publication_id):
        title = self._titles.get(str(publication_id))
        if title is None:
            return None
        return Publication(
            id=publication_id,
            professor_id=uuid4(),
            title=title,
            status=PublicationStatus.INDEXED,
        )

    async def save(self, publication):  # pragma: no cover - unused
        raise NotImplementedError

    async def clear_chunks(self, publication_id):  # pragma: no cover - unused
        raise NotImplementedError


class FakeReranker:
    def __init__(self, results: list[RerankResult]) -> None:
        self._results = results
        self.last_call: tuple | None = None

    async def rerank(self, query, documents, top_n=None):
        self.last_call = (query, documents, top_n)
        return self._results


def _row(chunk_text: str, publication_id: str, score: float) -> dict:
    return {
        "id": str(uuid4()),
        "publication_id": publication_id,
        "professor_id": str(uuid4()),
        "chunk_text": chunk_text,
        "distance": 1 - score,
        "score": score,
    }


@pytest.mark.asyncio
async def test_search_without_reranker_uses_vector_order_and_resolves_titles() -> None:
    pub_id = str(uuid4())
    rows = [_row("chunk about AI safety", pub_id, 0.9)]
    vector_store = FakeVectorStore(rows)
    repo = FakePublicationRepo({pub_id: "Attention Is All You Need"})

    retriever = PublicationRetriever(
        FakeLLMClient(), vector_store, repo, uuid4(), reranker=None, top_n=4
    )
    results = await retriever.search("AI safety")

    assert len(results) == 1
    assert results[0].chunk_text == "chunk about AI safety"
    assert results[0].source_title == "Attention Is All You Need"
    assert results[0].relevance_score == 0.9


@pytest.mark.asyncio
async def test_search_with_reranker_reorders_by_relevance() -> None:
    pub_a, pub_b = str(uuid4()), str(uuid4())
    rows = [_row("low relevance", pub_a, 0.3), _row("high relevance", pub_b, 0.5)]
    vector_store = FakeVectorStore(rows)
    repo = FakePublicationRepo({pub_a: "Paper A", pub_b: "Paper B"})
    # Reranker flips the order: index 1 ("high relevance") now ranks first.
    reranker = FakeReranker(
        [RerankResult(index=1, relevance_score=0.95), RerankResult(index=0, relevance_score=0.2)]
    )

    retriever = PublicationRetriever(
        FakeLLMClient(), vector_store, repo, uuid4(), reranker=reranker, top_n=2
    )
    results = await retriever.search("query")

    assert [r.chunk_text for r in results] == ["high relevance", "low relevance"]
    assert results[0].relevance_score == 0.95
    assert reranker.last_call[1] == ["low relevance", "high relevance"]


@pytest.mark.asyncio
async def test_search_returns_empty_when_no_chunks() -> None:
    vector_store = FakeVectorStore([])
    repo = FakePublicationRepo({})
    retriever = PublicationRetriever(FakeLLMClient(), vector_store, repo, uuid4())

    assert await retriever.search("anything") == []


@pytest.mark.asyncio
async def test_missing_title_falls_back_to_placeholder() -> None:
    pub_id = str(uuid4())
    vector_store = FakeVectorStore([_row("chunk", pub_id, 0.5)])
    repo = FakePublicationRepo({})  # no title registered

    retriever = PublicationRetriever(FakeLLMClient(), vector_store, repo, uuid4())
    results = await retriever.search("query")

    assert results[0].source_title == "Untitled publication"


@pytest.mark.asyncio
async def test_as_tool_is_invokable() -> None:
    pub_id = str(uuid4())
    vector_store = FakeVectorStore([_row("chunk", pub_id, 0.5)])
    repo = FakePublicationRepo({pub_id: "Some Paper"})
    retriever = PublicationRetriever(FakeLLMClient(), vector_store, repo, uuid4())

    tool = retriever.as_tool()
    result = await tool.ainvoke({"query": "AI safety"})

    assert result[0]["source_title"] == "Some Paper"
