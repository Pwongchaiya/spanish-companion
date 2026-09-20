"""Catch-all exposure-tier exception for unexpected SessionAudioService failures."""

from api.errors import ApiError


class SessionAudioServiceException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected session audio error occurred.",
            inner_exception,
        )
