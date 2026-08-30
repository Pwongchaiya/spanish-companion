"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class FlagValidationException(ApiError):
    """Wraps NotFoundFlagException for consumers, without leaking internals.

    Mirrors IngestionOrchestrationValidationException's shape
    (rag/models/ingestion/exceptions/ingestion_orchestration_validation_exception.py)
    -- only one leaf lands here, so no consumer-side discrimination is
    required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Flag validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
