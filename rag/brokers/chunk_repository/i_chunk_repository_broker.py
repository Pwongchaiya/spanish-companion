"""ChunkRepositoryBroker — storage contract for the `chunks` table."""

from typing import Protocol

from rag.models.orchestrations.retrieval import ScoredChunk


class ChunkRepositoryBroker(Protocol):
    """Storage contract for the `chunks` table."""

    def insert_chunk(
        self,
        topic: str,
        source_url: str,
        content: str,
        embedding: list[float],
        embedding_model_version: str,
        chunking_strategy_version: str,
    ) -> int:
        """Insert one row, return generated id. Ingestion's only write path."""
        ...

    def search_by_vector(self, embedding: list[float], top_k: int) -> list[ScoredChunk]:
        """Cosine-distance search (pgvector `<=>`), nearest-first, up to top_k rows.

        score here is the raw per-candidate distance from this one strategy —
        RankFusionStrategy overwrites it with the fused RRF rank downstream
        (built later, by a different feature).
        """
        ...
