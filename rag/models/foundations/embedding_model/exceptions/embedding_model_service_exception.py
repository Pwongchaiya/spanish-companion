"""Exposure-tier catch-all exception for EmbeddingModelService."""

from rag.errors import RagError


class EmbeddingModelServiceException(RagError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_service_exception.py's
    collapsed-tier shape one layer down: no intermediate Failed* tier --
    `inner_exception` is the raw Exception itself, one level in. This
    Foundation service sits directly on one broker, so every genuinely
    unexpected exception reaching the final catch is already raw; a Failed*
    tier would only wrap it in a second name that carries no extra
    information, same reasoning Ingestion's equivalent file records.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Embedding model service error occurred. Contact support.", inner_exception)
