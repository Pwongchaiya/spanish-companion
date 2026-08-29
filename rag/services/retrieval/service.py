"""Retrieval service — owns the hybrid search pipeline end to end.

    query -> embed -> [RetrievalStrategy, ...] -> RankFusionStrategy
          -> [ResultFilter, ...] -> top_k

Every stage is injected, so the shape above is fixed but each stage's
behaviour is swappable. Today exactly one strategy (dense) is wired and
fusion is a pass-through; LexicalStrategy and reranking are seams, not
placeholders — see strategies/fusion.py and strategies/filters.py.

Per the CLAUDE.md Phase 2 waiver this service depends on brokers directly:
there is no Foundation layer beneath it, so ORC-001 (dep count) and ORC-002
(no direct broker deps) do not apply.
"""

import logging
from typing import List, Optional, Sequence

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.models.retrieval import ScoredChunk
from rag.services.retrieval.strategies.dense import DenseVectorStrategy, RetrievalStrategy
from rag.services.retrieval.strategies.filters import CategoryBoostFilter, ResultFilter
from rag.services.retrieval.strategies.fusion import PassThroughRankFusion, RankFusionStrategy

logger = logging.getLogger(__name__)


class HybridRetrievalService:
    """Finds the corpus chunks that ground a Review Mode explanation.

    Direct dependencies are the embedding broker (query embedding) plus the
    pipeline stages it composes. The ChunkRepositoryBroker is passed in only
    to build the default DenseVectorStrategy — that strategy owns it, and
    this service never calls it.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModelBroker,
        chunk_repository: ChunkRepositoryBroker,
        strategies: Optional[Sequence[RetrievalStrategy]] = None,
        fusion: Optional[RankFusionStrategy] = None,
        filters: Optional[Sequence[ResultFilter]] = None,
    ) -> None:
        self._embedding_model = embedding_model
        # Defaults are the whole MVP pipeline, so app.py wires two brokers and
        # is done — no caller has to assemble stages by hand to get the
        # behaviour everything currently expects.
        self._strategies: Sequence[RetrievalStrategy] = (
            strategies if strategies is not None else [DenseVectorStrategy(chunk_repository)]
        )
        self._fusion: RankFusionStrategy = fusion if fusion is not None else PassThroughRankFusion()
        self._filters: Sequence[ResultFilter] = filters if filters is not None else []

    def retrieve(self, query: str, top_k: int, category: Optional[str] = None) -> List[ScoredChunk]:
        """Return up to top_k chunks grounding `query`, best-first.

        Args:
            query: the search text — for Review Mode, the flag's corrected text.
            top_k: maximum chunks to return. Owned by the caller (env-configured
                at the edge), never defaulted here.
            category: optional known-good topic hint (a flag's category). When
                given, chunks whose topic matches are floated to the front.

        Returns:
            Up to top_k chunks, or [] when the corpus has no match. Empty is a
            valid result, not an error — Review short-circuits on it before
            calling Generation.

        Raises:
            ValueError: blank query, or top_k < 1.

        Broker failures (SQLAlchemy/pgvector, model load) propagate unwrapped:
        this feature names no exception type of its own, and inventing one
        would be a contract decision, not an implementation detail.
        """
        if not query or not query.strip():
            raise ValueError("query is required")
        if top_k < 1:
            raise ValueError(f"top_k must be at least 1, got {top_k}")

        # Query text at DEBUG only (user speech); ids and counts at INFO.
        logger.debug("retrieve query=%r top_k=%d category=%r", query, top_k, category)

        query_embedding = self._embedding_model.embed([query])[0]

        # ponytail: each strategy is asked for exactly top_k, so a chunk the
        # category boost would have floated to rank 1 is invisible if dense
        # search ranked it top_k+1. Fine at MVP scale (3-5 topics, ~30
        # chunks). Upgrade path if Review Mode explanations cite the wrong
        # page: over-fetch here (top_k * a small factor) and keep the final
        # [:top_k] slice below exactly as it is.
        candidate_lists = [strategy.search(query_embedding, top_k) for strategy in self._strategies]

        fused = self._fusion.fuse(candidate_lists)

        # Configured filters first, then the per-call category boost — the
        # caller's hint for this specific query gets the final say on order.
        # CategoryBoostFilter is built per call rather than mutated, so no
        # stage carries request state between calls.
        pipeline: List[ResultFilter] = list(self._filters)
        if category is not None:
            pipeline.append(CategoryBoostFilter(category))

        for result_filter in pipeline:
            fused = result_filter.apply(fused)

        results = fused[:top_k]
        logger.info(
            "retrieve top_k=%d category=%r returned=%d ids=%s",
            top_k,
            category,
            len(results),
            [chunk.chunk_id for chunk in results],
        )
        return results
