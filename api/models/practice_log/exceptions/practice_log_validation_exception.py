"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class PracticeLogValidationException(ApiError):
    """Wraps InvalidPracticeAttemptException for consumers, without leaking
    internals.

    Mirrors rag.models.ingestion.exceptions.IngestionOrchestrationValidationException's
    shape ("Ingestion validation error..." -> "Practice log validation
    error..."). Only one leaf lands here, so no consumer-side
    discrimination is required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Practice log validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
