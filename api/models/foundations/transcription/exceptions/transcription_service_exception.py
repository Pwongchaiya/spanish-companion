"""Exposure-tier catch-all exception for TranscriptionService."""

from api.errors import ApiError


class TranscriptionServiceException(ApiError):
    """Catch-all wrapper for any unrecognised exception (mirrors PronunciationAssessmentServiceException)."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Transcription service error occurred. Contact support.", inner_exception)
