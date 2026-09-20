"""Catch-all exposure-tier exception for unexpected AudioStorageService failures."""

from api.errors import ApiError


class AudioStorageServiceException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected audio storage error occurred.",
            inner_exception,
        )
