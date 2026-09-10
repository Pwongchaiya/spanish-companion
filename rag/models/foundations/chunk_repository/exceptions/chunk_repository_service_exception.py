"""Exposure-tier catch-all exception for ChunkRepositoryService."""

from rag.errors import RagError


class ChunkRepositoryServiceException(RagError):
    """Catch-all wrapper for any exception not otherwise recognised -- the
    final safety net so nothing escapes this service unwrapped.

    Mirrors Ingestion's IngestionOrchestrationServiceException
    (rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_service_exception.py),
    one architectural layer down: Foundation instead of Orchestration. Same
    cited collapse of the Failed* tier -- `inner_exception` is the raw
    Exception itself, one level in, not a second named wrapper around it.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Chunk repository service error occurred. Contact support.", inner_exception)
