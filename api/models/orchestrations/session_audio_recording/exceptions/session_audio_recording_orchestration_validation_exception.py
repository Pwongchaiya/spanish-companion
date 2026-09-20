"""Exposure-tier exception wrapping a validation-tier wrapper (or a NotFound leaf) carried through whole."""

from api.errors import ApiError


class SessionAudioRecordingOrchestrationValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session audio recording validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
