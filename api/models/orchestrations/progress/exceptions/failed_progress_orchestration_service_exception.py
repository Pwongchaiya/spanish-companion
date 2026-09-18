"""Inner-tier exception for a genuinely unexpected failure."""

from api.errors import ApiError


class FailedProgressOrchestrationServiceException(ApiError):
    """Wraps a raw, unrecognised Exception before it is handed to
    _create_and_log_service_exception.

    Mirrors FailedLearnerProfileOrchestrationServiceException
    (api/models/orchestrations/learner_profile/exceptions/failed_learner_profile_orchestration_service_exception.py).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Failed progress orchestration service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
