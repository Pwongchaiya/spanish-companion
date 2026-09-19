"""Exposure-tier exception wrapping a validation-tier wrapper exception."""

from api.errors import ApiError


class PronunciationOrchestrationValidationException(ApiError):
    """Wraps PronunciationAssessmentValidationException (holding
    InvalidPronunciationAssessmentRequestException), carried through whole --
    the leaf sits at `.inner_exception.inner_exception`. Same role as
    ReviewOrchestrationValidationException
    (api/models/orchestrations/review/exceptions/review_orchestration_validation_exception.py:6-31).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation validation error occurred. Fix the errors and try again.",
            inner_exception=inner_exception,
        )
