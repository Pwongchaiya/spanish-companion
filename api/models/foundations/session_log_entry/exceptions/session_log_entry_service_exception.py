"""Exposure-tier catch-all for anything the other two tiers didn't classify."""

from api.errors import ApiError


class SessionLogEntryServiceException(ApiError):
    """Wraps any unexpected exception escaping SessionLogEntryService.
    Mirrors TopicCoveredServiceException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session log entry service error occurred, contact support.",
            inner_exception,
        )
