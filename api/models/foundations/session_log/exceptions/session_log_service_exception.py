"""Exposure-tier catch-all exception for SessionLogService."""

from api.errors import ApiError


class SessionLogServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised -- the
    final safety net so nothing escapes this service unwrapped.

    Mirrors FlagServiceException's shape; the Failed* tier is collapsed away
    for the same reason: this service sits directly on a broker, so anything
    reaching the final catch is already raw.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Session log service error occurred. Contact support.", inner_exception)
