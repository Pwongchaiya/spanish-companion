"""Exposure-tier catch-all exception for LearnerProfileOrchestrationService."""

from api.errors import ApiError


class LearnerProfileOrchestrationServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors ReviewOrchestrationServiceException
    (api/models/orchestrations/review/exceptions/review_orchestration_service_exception.py).
    `inner_exception` here is always a
    FailedLearnerProfileOrchestrationServiceException, and the raw cause is
    one level further in.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Learner profile orchestration service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
