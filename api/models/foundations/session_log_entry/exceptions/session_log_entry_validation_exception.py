"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class SessionLogEntryValidationException(ApiError):
    """Wraps InvalidSessionLogEntryException /
    NotFoundSessionLogEntryException for consumers, without leaking
    internals. Mirrors TopicCoveredValidationException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session log entry validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
