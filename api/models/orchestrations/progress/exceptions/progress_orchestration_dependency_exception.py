"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class ProgressOrchestrationDependencyException(ApiError):
    """Wraps a dependency-tier failure raised by one of this service's three
    dependencies (LearnerProfile Processing, MistakePattern/TopicCovered
    Foundation).

    What lands here is LearnerProfileDependencyException,
    MistakePatternDependencyException, or TopicCoveredDependencyException --
    each already wrapping its own storage-failure leaf one level further in.

    Mirrors LearnerProfileOrchestrationDependencyException's shape
    (api/models/orchestrations/learner_profile/exceptions/learner_profile_orchestration_dependency_exception.py).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Progress orchestration dependency error occurred. Contact support.",
            inner_exception=inner_exception,
        )
