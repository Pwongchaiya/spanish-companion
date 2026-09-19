"""Exposure-tier catch-all exception for PronunciationOrchestrationService."""

from api.errors import ApiError


class PronunciationOrchestrationServiceException(ApiError):
    """Catch-all wrapper; `inner_exception` is always a
    FailedPronunciationOrchestrationServiceException. Same role as
    ReviewOrchestrationServiceException
    (api/models/orchestrations/review/exceptions/review_orchestration_service_exception.py:6-25).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
