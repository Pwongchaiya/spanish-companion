"""Exposure-tier catch-all; `inner_exception` is always the Failed* intermediate."""

from api.errors import ApiError


class SessionAudioRecordingOrchestrationServiceException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session audio recording service error occurred. Contact support.",
            inner_exception,
        )
