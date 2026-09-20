"""Exposure-tier wrapper for InvalidSessionAudioException / NotFoundSessionAudioException."""

from api.errors import ApiError


class SessionAudioValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session audio validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
