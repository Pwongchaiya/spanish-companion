"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class FlagValidationException(ApiError):
    """Wraps NotFoundFlagException or InvalidFlagStatusException for
    consumers, without leaking internals.

    Mirrors IngestionOrchestrationValidationException's shape
    (rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_validation_exception.py).
    Two leaves land here as of 2026-09-24 (InvalidFlagStatusException added
    alongside NotFoundFlagException) -- callers that need to discriminate
    (e.g. the 404-vs-400 branch in api/exposers/review.py) do so with
    isinstance() on `.inner_exception`, same as every other multi-leaf
    wrapper in this codebase (e.g. ReviewOrchestrationValidationException).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Flag validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
