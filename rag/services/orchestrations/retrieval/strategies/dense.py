"""Retrieval strategies — the candidate-producing stage of hybrid search.

One strategy = one way of finding candidate chunks for a query. Today there
is exactly one (dense vector search over pgvector). `LexicalStrategy` (BM25 /
tsvector) is a deferred seam per the Phase 2 architecture decision record:
when it lands it implements this same Protocol and is appended to
HybridRetrievalService's `strategies` list — no change to the service, the
fusion stage's interface, or the filters.
"""

from typing import List, Protocol

from rag.brokers.logging import LoggingBroker
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository import IChunkRepositoryService


class RetrievalStrategy(Protocol):
    """One candidate-producing search path.

    Every strategy takes the *already-embedded* query, so the query is
    embedded exactly once per retrieve() call no matter how many strategies
    run. A future lexical strategy simply ignores the embedding and searches
    the raw text it was constructed with — the Protocol does not change.
    """

    def search(self, query_embedding: List[float], top_k: int) -> List[ScoredChunk]:
        """Return up to top_k candidates, best-first by this strategy's own ranking.

        `ScoredChunk.score` carries whatever this strategy's native score is
        (for dense: raw cosine distance, lower = closer). Scores are only
        comparable *within* one strategy's list — never across strategies.
        That is precisely why fusion merges by rank, not by score.
        """
        ...


class DenseVectorStrategy:
    """Dense vector search via pgvector cosine distance.

    Owns the ChunkRepository Foundation service — the orchestration service
    never touches it directly, so swapping in a different candidate source
    touches only this class.

    No exception handling here: ChunkRepositoryService already wraps its own
    broker failures (ChunkRepositoryDependencyException et al), and those
    propagate raw through this class to be caught one level up in
    HybridRetrievalServiceExceptions._try_catch.
    """

    def __init__(
        self,
        chunk_repository_service: IChunkRepositoryService,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._chunk_repository_service = chunk_repository_service
        self._logging_broker = logging_broker

    def search(self, query_embedding: List[float], top_k: int) -> List[ScoredChunk]:
        candidates = self._chunk_repository_service.search_by_vector(query_embedding, top_k)

        # Per rag-retrieval-skill: every strategy logs its own candidates
        # before fusion — when a Review Mode explanation cites the wrong RAE
        # page, this line is where debugging starts. Chunk ids + scores only;
        # the query text itself is logged by the service at DEBUG.
        self._logging_broker.log_debug(
            "DenseVectorStrategy top_k=%d candidates=%s",
            top_k,
            [(chunk.chunk_id, chunk.topic, round(chunk.score, 4)) for chunk in candidates],
        )
        return candidates
