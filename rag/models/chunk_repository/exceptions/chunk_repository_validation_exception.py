"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from rag.errors import RagError


class ChunkRepositoryValidationException(RagError):
    """Wraps InvalidChunkRepositoryInputError for consumers, without leaking internals.

    Mirrors Ingestion's IngestionOrchestrationValidationException
    (rag/models/ingestion/exceptions/ingestion_orchestration_validation_exception.py),
    one architectural layer down: Foundation instead of Orchestration. Only
    one leaf lands here (InvalidChunkRepositoryInputError), so no
    consumer-side discrimination is required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Chunk repository validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
