"""Leaf validation exception raised by EmbeddingModelService's input checks."""

from rag.errors import RagError


class InvalidEmbeddingModelInputError(RagError):
    """Raised when `embed`'s input is unusable.

    Two raise sites, both in embedding_model_service_validations.py: an empty
    `texts` list, or any element that is blank/whitespace-only.

    Mirrors rag/models/ingestion/exceptions/ingestion_validation_error.py's
    shape -- message-only constructor, no inner_exception, raised from a
    named validation method.

    Leaf exception -- always caught and wrapped into
    EmbeddingModelValidationException before leaving the service, mirroring
    IngestionServiceExceptions._try_catch's IngestionValidationError handling
    one layer up.
    """
