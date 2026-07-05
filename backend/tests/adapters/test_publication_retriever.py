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
        self.calls = 0

    async def rerank(self, query, documents, top_n=None):
        self.calls += 1
        self.last_call = (query, documents, top_n)
        # Default identity ordering if the scripted results don't match the
        # candidate count (keeps index-based selection in range for new tests).
        if len(self._results) != len(documents):
            return [
                RerankResult(index=i, relevance_score=1.0 - i * 0.1)
                for i in range(min(len(documents), top_n or len(documents)))
            ]
        return self._results


class CountingLLMClient:
    """Embeds like the fake, but counts calls — proves the cache skips embedding
    on a repeat query, not just the rerank."""

    def __init__(self) -> None:
        self.embed_calls = 0

    async def embed(self, text: str) -> list[float]:
        self.embed_calls += 1
        return [0.1, 0.2, 0.3]

    async def complete(self, messages, model=None):  # pragma: no cover - unused
        raise NotImplementedError


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
    # A query long enough to clear the complexity gate so rerank actually runs.
    results = await retriever.search("does this candidate genuinely overlap with the corpus")

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


# --- Rerank-conservation levers ------------------------------------------


def _retriever_with_reranker(reranker: FakeReranker, llm=None) -> PublicationRetriever:
    pub_id = str(uuid4())
    rows = [_row(f"chunk {i}", pub_id, 0.9 - i * 0.1) for i in range(8)]
    return PublicationRetriever(
        llm or FakeLLMClient(),
        FakeVectorStore(rows),
        FakePublicationRepo({pub_id: "Some Paper"}),
        uuid4(),
        reranker=reranker,
        top_n=4,
    )


@pytest.mark.asyncio
async def test_short_query_skips_rerank(monkeypatch) -> None:  # noqa: ANN001
    from src.config import get_settings

    monkeypatch.setattr(get_settings(), "RERANK_MIN_QUERY_WORDS", 6)
    reranker = FakeReranker([])
    retriever = _retriever_with_reranker(reranker)

    # 3 words — under the threshold, so vector order is used and no rerank fires.
    await retriever.search("short simple query")

    assert reranker.calls == 0


@pytest.mark.asyncio
async def test_long_query_reranks(monkeypatch) -> None:  # noqa: ANN001
    from src.config import get_settings

    monkeypatch.setattr(get_settings(), "RERANK_MIN_QUERY_WORDS", 6)
    reranker = FakeReranker([])
    retriever = _retriever_with_reranker(reranker)

    await retriever.search("this is a genuinely long and ambiguous research query")

    assert reranker.calls == 1


@pytest.mark.asyncio
async def test_tool_retrievals_never_rerank(monkeypatch) -> None:  # noqa: ANN001
    from src.config import get_settings

    monkeypatch.setattr(get_settings(), "RERANK_MIN_QUERY_WORDS", 0)  # would rerank everything
    reranker = FakeReranker([])
    retriever = _retriever_with_reranker(reranker)

    tool = retriever.as_tool()
    # Even a long query via the debater tool path must skip rerank.
    await tool.ainvoke({"query": "a long query that would otherwise clear the gate"})

    assert reranker.calls == 0


@pytest.mark.asyncio
async def test_repeat_query_served_from_cache(monkeypatch) -> None:  # noqa: ANN001
    from src.config import get_settings

    monkeypatch.setattr(get_settings(), "RERANK_MIN_QUERY_WORDS", 0)
    reranker = FakeReranker([])
    llm = CountingLLMClient()
    retriever = _retriever_with_reranker(reranker, llm=llm)

    q = "same query asked twice in one debate"
    first = await retriever.search(q)
    second = await retriever.search(q)

    assert first == second
    # Only the first call embeds + reranks; the second is a cache hit.
    assert llm.embed_calls == 1
    assert reranker.calls == 1


@pytest.mark.asyncio
async def test_cache_key_separates_rerank_and_tool_paths(monkeypatch) -> None:  # noqa: ANN001
    from src.config import get_settings

    monkeypatch.setattr(get_settings(), "RERANK_MIN_QUERY_WORDS", 0)
    reranker = FakeReranker([])
    retriever = _retriever_with_reranker(reranker)

    q = "identical query text over both paths"
    await retriever.search(q, allow_rerank=True)   # baseline path → reranks
    await retriever.search(q, allow_rerank=False)  # tool path → no rerank

    # Same text but different allow_rerank must not collide in the cache: the
    # reranked result must never be served to a no-rerank tool call and vice
    # versa. Exactly one rerank happened (the baseline call).
    assert reranker.calls == 1
