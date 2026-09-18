"""Exposure-tier catch-all exception for ProgressOrchestrationService."""

from api.errors import ApiError


class ProgressOrchestrationServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    Mirrors LearnerProfileOrchestrationServiceException
    (api/models/orchestrations/learner_profile/exceptions/learner_profile_orchestration_service_exception.py).
    `inner_exception` here is always a
    FailedProgressOrchestrationServiceException, and the raw cause is one
    level further in.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Progress orchestration service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
