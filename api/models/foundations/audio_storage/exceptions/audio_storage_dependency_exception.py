"""Exposure-tier wrapper for FailedAudioStorageException."""

from api.errors import ApiError


class AudioStorageDependencyException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Audio storage is currently unavailable. Try again shortly.",
            inner_exception,
        )
