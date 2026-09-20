"""Exposure-tier wrapper for FailedSessionAudioStorageException."""

from api.errors import ApiError


class SessionAudioDependencyException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session audio data is currently unavailable. Try again shortly.",
            inner_exception,
        )
