"""Exposure-tier catch-all exception for PracticeLogService."""

from api.errors import ApiError


class PracticeLogServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised -- the
    final safety net so nothing escapes this service unwrapped.

    Follows the Session Lifecycle precedent
    (api/models/session_lifecycle/exceptions/session_service_exception.py)
    of collapsing the Failed* tier away rather than the Ingestion one that
    keeps it -- Practice Log sits directly on one broker with no layer
    beneath it worth distinguishing further, so `inner_exception` is the
    raw Exception itself, one level in.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Practice log service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
