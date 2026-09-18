"""Inner-tier exception for a genuinely unexpected failure."""

from api.errors import ApiError


class FailedLearnerProfileOrchestrationServiceException(ApiError):
    """Wraps a raw, unrecognised Exception before it is handed to
    _create_and_log_service_exception.

    Mirrors FailedReviewOrchestrationServiceException
    (api/models/orchestrations/review/exceptions/failed_review_orchestration_service_exception.py).
    Also the tier any of the three Foundation/Processing *ServiceException
    catch-alls (LearnerProfileServiceException, MistakePatternServiceException,
    TopicCoveredServiceException) fall into -- none of the three is caught by
    name, same precedent as Review not catching Flag/PracticeLog's own
    *ServiceException classes by name.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Failed learner profile orchestration service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
