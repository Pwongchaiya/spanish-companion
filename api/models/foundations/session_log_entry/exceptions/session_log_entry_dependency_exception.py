"""Exposure-tier exception wrapping a dependency-tier leaf exception."""

from api.errors import ApiError


class SessionLogEntryDependencyException(ApiError):
    """Wraps FailedSessionLogEntryStorageException for consumers, without
    leaking the raw SQLAlchemy error. Mirrors
    TopicCoveredDependencyException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session log entry dependency error occurred, contact support.",
            inner_exception,
        )
