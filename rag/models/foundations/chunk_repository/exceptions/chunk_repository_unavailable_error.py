"""Leaf dependency exception raised when the ChunkRepositoryBroker call fails."""

from rag.errors import RagError


class ChunkRepositoryUnavailableError(RagError):
    """Raised when the underlying chunk store is unreachable.

    Name and shape mirror Ingestion's IngestionUnavailableError
    (rag/models/orchestrations/ingestion/exceptions/ingestion_unavailable_error.py) --
    raised at the two broker call sites in _ChunkRepositoryServiceBase
    (`insert_chunk`, `search_by_vector`), same
    `raise ChunkRepositoryUnavailableError(str(e)) from e` shape as
    Ingestion's two broker call sites.

    Leaf exception -- always caught and wrapped into
    ChunkRepositoryDependencyException before leaving the service, mirroring
    Ingestion's IngestionUnavailableError -> IngestionOrchestrationDependencyException.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
