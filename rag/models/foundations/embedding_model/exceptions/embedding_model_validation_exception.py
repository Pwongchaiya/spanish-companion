"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from rag.errors import RagError


class EmbeddingModelValidationException(RagError):
    """Wraps InvalidEmbeddingModelInputError for consumers, without leaking internals.

    Mirrors rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_validation_exception.py's
    shape one layer down, at the Foundation tier: message + inner_exception,
    produced by EmbeddingModelServiceExceptions._create_and_log_validation_exception.
    Only one leaf lands here, so no consumer-side discrimination is required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Embedding model validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
