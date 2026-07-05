from __future__ import annotations

from uuid import UUID

from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel

from src.application.ports.outbound.llm_client import LLMClient
from src.application.ports.outbound.repository import PublicationRepository
from src.application.ports.outbound.reranker import Reranker
from src.application.ports.outbound.vector_store import VectorStore
from src.config import get_settings


class RetrievedChunk(BaseModel):
    chunk_text: str
    source_title: str
    relevance_score: float | None = None


class PublicationRetriever:
    """RAG over the professor's own indexed corpus (ActionKind.RETRIEVAL).

    Scoped to one `professor_id` per instance — the debate is always evaluated
    against a single professor's indexed publications, never a global corpus.
    Re-ranks the initial vector-search candidates via `qwen3-rerank` when a
    `Reranker` is supplied; falls back to raw vector-similarity order otherwise.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        vector_store: VectorStore,
        publication_repo: PublicationRepository,
        professor_id: UUID,
        reranker: Reranker | None = None,
        candidate_k: int = 8,
        top_n: int = 4,
    ) -> None:
        self._llm_client = llm_client
        self._vector_store = vector_store
        self._publication_repo = publication_repo
        self._professor_id = professor_id
        self._reranker = reranker
        self._candidate_k = candidate_k
        self._top_n = top_n
        # Debate-scoped cache: the retriever is rebuilt per debate, so this dict
        # lives for exactly one debate and needs no TTL. Keyed by (query,
        # allow_rerank) so a repeated query in the same debate doesn't re-embed
        # or re-rerank. See levers below.
        self._cache: dict[tuple[str, bool], list[RetrievedChunk]] = {}

    def _should_rerank(self, query: str, allow_rerank: bool) -> bool:
        """Whether to spend a rerank call on this query. We conserve the scarce
        free rerank quota three ways: the caller can forbid it (tool retrievals
        do — only the one baseline retrieval per debate reranks), a reranker
        must be wired at all, and a short/simple query rides raw vector order."""
        if not allow_rerank or self._reranker is None:
            return False
        min_words = get_settings().RERANK_MIN_QUERY_WORDS
        return len(query.split()) >= min_words

    async def search(self, query: str, *, allow_rerank: bool = True) -> list[RetrievedChunk]:
        cache_key = (query, allow_rerank)
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("  ↳ retrieval cache hit (no rerank/embed call)")
            return cached

        embedding = await self._llm_client.embed(query)
        raw = await self._vector_store.query(
            embedding, self._professor_id, top_k=self._candidate_k
        )
        if not raw:
            self._cache[cache_key] = []
            return []

        selected: list[tuple[dict, float | None]]
        if self._should_rerank(query, allow_rerank):
            texts = [r["chunk_text"] for r in raw]
            ranked = await self._reranker.rerank(query, texts, top_n=self._top_n)  # type: ignore[union-attr]
            selected = [(raw[r.index], r.relevance_score) for r in ranked]
        else:
            selected = [(r, r.get("score")) for r in raw[: self._top_n]]

        titles = await self._resolve_titles({chunk["publication_id"] for chunk, _ in selected})
        results = [
            RetrievedChunk(
                chunk_text=chunk["chunk_text"],
                source_title=titles.get(chunk["publication_id"], "Untitled publication"),
                relevance_score=score,
            )
            for chunk, score in selected
        ]
        self._cache[cache_key] = results
        return results

    async def _resolve_titles(self, publication_ids: set[str]) -> dict[str, str]:
        titles: dict[str, str] = {}
        for pub_id in publication_ids:
            pub = await self._publication_repo.get(UUID(pub_id))
            if pub and pub.title:
                titles[pub_id] = pub.title
        return titles

    def as_tool(self):
        @tool
        async def retrieve_from_professor_corpus(query: str) -> list[dict]:
            """Search the professor's own indexed publications for content
            relevant to `query`. Use this to check whether a candidate's
            claimed research area or background genuinely overlaps with the
            professor's own published work."""
            # Mid-debate tool retrievals skip rerank — they're narrower
            # follow-ups on top of the already-reranked baseline, and reranking
            # every one of them is what burns the scarce free rerank quota.
            results = await self.search(query, allow_rerank=False)
            return [r.model_dump() for r in results]

        return retrieve_from_professor_corpus
