"""Shared retrieval result type.

One dataclass used end-to-end: ChunkRepositoryBroker.search_by_vector returns
it, Retrieval's strategies/fusion/filters transform it, Generation and Review
consume it. Pinned in the Phase 2 architecture decision record — do not
narrow it or split it into a separate broker-only type.
"""

from dataclasses import dataclass


@dataclass
class ScoredChunk:
    chunk_id: int
    topic: str
    source_url: str
    content: str
    score: float
