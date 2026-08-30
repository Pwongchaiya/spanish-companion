"""Interface for the Ingestion orchestration service.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
IEntitlementCodesOrchestrationService.cs:10-13 -- typing.Protocol, not
abc.ABC, per this project's broker-interface waiver (CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers table), extended to service interfaces the same
way api/services/session_lifecycle/i_session_lifecycle_service.py and
api/services/review/i_review_service.py do: the reference project itself
co-locates the interface file with its implementation in the same folder.

Cited naming divergence: Session Lifecycle and Review both drop the C# `I`
prefix from the class (Protocol `SessionLifecycleService` -> concrete
`ConversationSessionService`; Protocol `ReviewService` -> concrete
`ReviewOrchestrator`), keeping it only in the file name. That works there
because the feature name was free -- the concrete class had a different name.
Here the concrete class must stay `IngestionService` (its public name,
imported by rag/controllers/ingestion.py:26 and by three test modules), so the
feature name is taken. This Protocol therefore keeps the reference's literal
`I` prefix: `IIngestionService`, exactly as
IEntitlementCodesOrchestrationService.cs:10 spells it.
"""

from typing import Protocol


class IIngestionService(Protocol):
    """External-facing contract for the Ingestion orchestration service."""

    def ingest_topic(self, topic: str, source_url: str, text: str) -> int:
        """Chunk `text`, embed the chunks in one batch, insert each. Returns rows inserted.

        Empty or whitespace-only `text` yields zero chunks and returns 0
        without touching either broker.

        Raises:
            IngestionOrchestrationValidationException: wrapping
                IngestionValidationError -- blank `topic`, blank `source_url`,
                or an embedding batch whose length does not match the chunk
                batch.
            IngestionOrchestrationDependencyException: wrapping
                IngestionUnavailableError -- the chunk store or embedding
                model is unreachable.
            IngestionOrchestrationServiceException: anything else.
        """
        ...


__all__ = ["IIngestionService"]
