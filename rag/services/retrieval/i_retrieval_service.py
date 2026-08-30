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
existing name (`HybridRetrievalService`).
"""

from typing import List, Optional, Protocol

from rag.models.retrieval import ScoredChunk


class RetrievalService(Protocol):
    """External-facing contract for Retrieval's orchestration service."""

    def retrieve(self, query: str, top_k: int, category: Optional[str] = None) -> List[ScoredChunk]:
        """Return up to top_k chunks grounding `query`, best-first.

        Returns [] when the corpus has no match -- empty is a valid result,
        not an error.

        Raises RetrievalOrchestrationDependencyException (wrapping
        RetrievalUnavailableError) if the chunk store or embedding model is
        unreachable, or RetrievalOrchestrationServiceException for anything
        else.

        Raises a bare ValueError for a blank query or top_k < 1. That is
        deliberately NOT wrapped: it is a programming error at the call
        site, not a condition a caller is expected to handle.
        """
        ...


__all__ = ["RetrievalService"]
