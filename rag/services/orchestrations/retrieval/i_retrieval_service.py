"""Interface for the Retrieval orchestration service.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
IEntitlementCodesOrchestrationService.cs:10-13 -- typing.Protocol, not
abc.ABC, per this project's broker-interface waiver (CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers table), extended to service interfaces the
same way api/services/review/i_review_service.py and
api/services/session_lifecycle/i_session_lifecycle_service.py do: the
reference project itself co-locates the interface file with its
implementation in the same folder.

Naming follows the Session Lifecycle / Review precedent -- the Protocol is
named for the feature (`RetrievalService`) and the concrete class keeps its
existing name (`HybridRetrievalOrchestrationService`).
"""

from typing import List, Optional, Protocol

from rag.models.orchestrations.retrieval import ScoredChunk


class RetrievalService(Protocol):
    """External-facing contract for Retrieval's orchestration service."""

    def retrieve(self, query: str, top_k: int, category: Optional[str] = None) -> List[ScoredChunk]:
        """Return up to top_k chunks grounding `query`, best-first.

        Returns [] when the corpus has no match -- empty is a valid result,
        not an error.

        Raises RetrievalOrchestrationValidationException (wrapping
        RetrievalValidationError) for a blank query or top_k < 1,
        RetrievalOrchestrationDependencyException (wrapping the
        Foundation tier's EmbeddingModelDependencyException or
        ChunkRepositoryDependencyException) if the chunk store or embedding
        model is unreachable, or RetrievalOrchestrationServiceException for
        anything else.
        """
        ...


__all__ = ["RetrievalService"]
