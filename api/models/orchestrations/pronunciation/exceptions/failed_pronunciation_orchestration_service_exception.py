"""Inner-tier exception for a genuinely unexpected failure."""

from api.errors import ApiError


class FailedPronunciationOrchestrationServiceException(ApiError):
    """Wraps a raw, unrecognised Exception before it is handed to
    CreateAndLogServiceException. Same role as
    FailedReviewOrchestrationServiceException
    (api/models/orchestrations/review/exceptions/failed_review_orchestration_service_exception.py:6-25);
    the raw cause stays reachable at `service_exception.inner_exception.inner_exception`.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Failed pronunciation service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
