"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class TranscriptionValidationException(ApiError):
    """Wraps InvalidTranscriptionRequestException (mirrors PronunciationAssessmentValidationException)."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Transcription validation error occurred. Fix the errors and try again.", inner_exception)
