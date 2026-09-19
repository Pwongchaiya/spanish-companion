"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class PronunciationOrchestrationDependencyException(ApiError):
    """Wraps PronunciationAssessmentDependencyException (Azure unreachable) or
    PronunciationResultDependencyException (storage failed after a successful
    assessment), carried through whole. Same role as
    ReviewOrchestrationDependencyException
    (api/models/orchestrations/review/exceptions/review_orchestration_dependency_exception.py:6-38).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation dependency error occurred. Contact support.",
            inner_exception=inner_exception,
        )
