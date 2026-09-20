"""Exposure-tier catch-all; `inner_exception` is always the Failed* intermediate."""

from api.errors import ApiError


class SessionReplayOrchestrationServiceException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session replay service error occurred. Contact support.",
            inner_exception,
        )
