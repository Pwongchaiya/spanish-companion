"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class PronunciationAssessmentDependencyException(ApiError):
    """Wraps PronunciationAssessmentUnavailableError (mirrors TtsDependencyException)."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Pronunciation assessment dependency error occurred. Contact support.", inner_exception)
