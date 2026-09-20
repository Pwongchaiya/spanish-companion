"""Catch-all exposure-tier exception for unexpected IngestionQueueService failures."""

from api.errors import ApiError


class IngestionQueueServiceException(ApiError):
    """Wraps any exception not covered by the validation/dependency leaves --
    IngestionQueueService's safety net.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected ingestion queue error occurred.",
            inner_exception,
        )
