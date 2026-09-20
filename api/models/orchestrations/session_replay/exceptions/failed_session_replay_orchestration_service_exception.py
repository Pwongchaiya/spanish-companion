"""Inner-tier exception wrapping a raw, unrecognised Exception."""

from api.errors import ApiError


class FailedSessionReplayOrchestrationServiceException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Failed Session replay service error occurred. Contact support.",
            inner_exception,
        )
