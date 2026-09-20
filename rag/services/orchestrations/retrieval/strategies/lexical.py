"""Lexical (keyword) retrieval strategy -- the second-opinion search path.

Unlike DenseVectorStrategy it takes the raw query text, not an embedding, so
it has its own Protocol instead of widening RetrievalStrategy. It is NOT in
the default `strategies` list: Retrieval only calls it when a caller asks
for the alternate pass (Review's second-opinion retry after a rejected
grounding verdict), so default retrieval stays dense-only and unchanged.

No exception handling: ChunkRepositoryService wraps its own broker failures
and they propagate to HybridRetrievalOrchestrationServiceExceptions._try_catch.
"""

from typing import List, Protocol

from rag.brokers.logging import LoggingBroker
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository import IChunkRepositoryService


class TextRetrievalStrategy(Protocol):
    """A candidate-producing search path that works from the raw query text."""

    def search_text(self, query: str, top_k: int) -> List[ScoredChunk]:
        """Return up to top_k candidates, best-first by this strategy's own ranking."""
        ...


class LexicalStrategy:
    """Postgres full-text search over chunk content (score = ts_rank, higher = better)."""

    def __init__(
        self,
        chunk_repository_service: IChunkRepositoryService,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._chunk_repository_service = chunk_repository_service
        self._logging_broker = logging_broker

    def search_text(self, query: str, top_k: int) -> List[ScoredChunk]:
        candidates = self._chunk_repository_service.search_by_text(query, top_k)
        self._logging_broker.log_debug(
            "LexicalStrategy top_k=%d candidates=%s",
            top_k,
            [(chunk.chunk_id, chunk.topic, round(chunk.score, 4)) for chunk in candidates],
        )
        return candidates
