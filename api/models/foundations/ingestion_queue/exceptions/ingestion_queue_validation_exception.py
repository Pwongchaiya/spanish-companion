"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class IngestionQueueValidationException(ApiError):
    """Wraps InvalidIngestionQueueException / NotFoundIngestionQueueException
    for consumers, without leaking internals.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Ingestion queue validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
