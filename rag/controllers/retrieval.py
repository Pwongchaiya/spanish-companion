"""In-process controller for the Retrieval feature.

Not HTTP — called directly by api/services/review.py's ReviewOrchestrator
(built later). Thin pass-through per CLAUDE.md's Phase 2 Layer-Agent
Mapping: versioning and HTTP status-code mapping are waived here since
there is no HTTP response to map.
"""

from typing import List, Optional

from rag.models.retrieval import ScoredChunk
from rag.services.orchestrations.retrieval import HybridRetrievalService


class RetrievalController:
    """Public entry point for Retrieval. No logic beyond delegation."""

    def __init__(self, service: HybridRetrievalService) -> None:
        self._service = service

    def retrieve(self, query: str, top_k: int, category: Optional[str] = None) -> List[ScoredChunk]:
        return self._service.retrieve(query, top_k, category)
