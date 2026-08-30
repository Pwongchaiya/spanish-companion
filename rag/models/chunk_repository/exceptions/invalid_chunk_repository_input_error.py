"""Leaf validation exception raised by ChunkRepositoryService's input checks."""

from rag.errors import RagError


class InvalidChunkRepositoryInputError(RagError):
    """Raised when insert_chunk/search_by_vector input is unusable.

    Four raise sites, all in chunk_repository_service_validations.py: blank
    `topic`, blank `source_url`, blank `content` (all three checked by
    `_validate_insert_chunk_input`), and `top_k < 1` (checked by
    `_validate_search_input`).

    Mirrors Ingestion's IngestionValidationError
    (rag/models/ingestion/exceptions/ingestion_validation_error.py) --
    message-only constructor, no inner_exception, raised from named
    validation methods, one architectural layer down: Foundation instead of
    Orchestration, wrapping a broker directly rather than two.

    Leaf exception -- always caught and wrapped into
    ChunkRepositoryValidationException before leaving the service, mirroring
    Ingestion's IngestionValidationError -> IngestionOrchestrationValidationException.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
