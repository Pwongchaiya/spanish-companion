"""Exposure-tier exception wrapping a failed broker call."""

from rag.errors import RagError


class ChunkRepositoryDependencyException(RagError):
    """Wraps ChunkRepositoryUnavailableError -- the broker this service depends on failed.

    Mirrors Ingestion's IngestionOrchestrationDependencyException
    (rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_dependency_exception.py),
    one architectural layer down: Foundation instead of Orchestration,
    wrapping one broker directly rather than two. Same cited omission of a
    DependencyValidation tier -- a broker failure here is an infrastructure
    outage, never a rejected input bubbled up from a layer beneath (there is
    no layer beneath a Foundation service).

    ChunkRepositoryUnavailableError IS the leaf, so it is carried through
    whole as `inner_exception` rather than unwrapped, matching Ingestion's
    identical divergence note.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Chunk repository dependency error occurred. Contact support.", inner_exception)
