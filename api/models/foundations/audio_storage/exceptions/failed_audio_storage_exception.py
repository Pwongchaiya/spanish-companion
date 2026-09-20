"""Leaf dependency exception raised when an IAudioStorageBroker call fails."""

from api.errors import ApiError


class FailedAudioStorageException(ApiError):
    """Any OSError from the broker. Wrapped into AudioStorageDependencyException."""
