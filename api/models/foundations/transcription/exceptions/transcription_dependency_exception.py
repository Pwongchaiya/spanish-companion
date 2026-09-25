"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class TranscriptionDependencyException(ApiError):
    """Wraps TranscriptionUnavailableError (mirrors PronunciationAssessmentDependencyException)."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Transcription dependency error occurred. Contact support.", inner_exception)
