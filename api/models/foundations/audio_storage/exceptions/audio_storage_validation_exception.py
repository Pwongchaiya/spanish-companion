"""Exposure-tier wrapper for InvalidAudioStorageException."""

from api.errors import ApiError


class AudioStorageValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Audio storage validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
