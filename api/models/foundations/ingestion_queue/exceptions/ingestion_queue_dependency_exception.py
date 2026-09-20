"""Exposure-tier exception wrapping a broker-failure leaf exception."""

from api.errors import ApiError


class IngestionQueueDependencyException(ApiError):
    """Wraps FailedIngestionQueueStorageException for consumers, without
    leaking internals.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Ingestion queue data is currently unavailable. Try again shortly.",
            inner_exception,
        )
