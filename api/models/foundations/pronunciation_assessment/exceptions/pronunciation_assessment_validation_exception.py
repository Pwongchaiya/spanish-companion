"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class PronunciationAssessmentValidationException(ApiError):
    """Wraps InvalidPronunciationAssessmentRequestException (mirrors TtsValidationException)."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation assessment validation error occurred. Fix the errors and try again.", inner_exception
        )
