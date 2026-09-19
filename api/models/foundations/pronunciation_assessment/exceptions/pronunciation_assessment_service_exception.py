"""Exposure-tier catch-all exception for PronunciationAssessmentService."""

from api.errors import ApiError


class PronunciationAssessmentServiceException(ApiError):
    """Catch-all wrapper for any unrecognised exception (mirrors TtsServiceException)."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Pronunciation assessment service error occurred. Contact support.", inner_exception)
