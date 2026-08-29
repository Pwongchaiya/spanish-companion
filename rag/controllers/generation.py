"""In-process controller for the Generation feature.

Not HTTP — called directly by api/services/review.py's ReviewOrchestrator
(built later). Thin pass-through per CLAUDE.md's Phase 2 Layer-Agent
Mapping: versioning and HTTP status-code mapping are waived here since
there is no HTTP response to map.
"""

from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk
from rag.services.generation import FlagLike, GenerationService


class GenerationController:
    """Public entry point for Generation. No logic beyond delegation."""

    def __init__(self, service: GenerationService) -> None:
        self._service = service

    def explain(self, flag: FlagLike, chunk: ScoredChunk) -> Explanation:
        return self._service.explain(flag, chunk)
