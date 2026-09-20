"""Leaf dependency exception raised when an ISessionAudioBroker call fails."""

from api.errors import ApiError


class FailedSessionAudioStorageException(ApiError):
    """Any SQLAlchemyError from the broker. Wrapped into SessionAudioDependencyException."""
