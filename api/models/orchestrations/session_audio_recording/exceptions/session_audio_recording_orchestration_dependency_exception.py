"""Exposure-tier exception wrapping a Foundation-tier dependency exception."""

from api.errors import ApiError


class SessionAudioRecordingOrchestrationDependencyException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session audio recording dependency error occurred. Contact support.",
            inner_exception,
        )
