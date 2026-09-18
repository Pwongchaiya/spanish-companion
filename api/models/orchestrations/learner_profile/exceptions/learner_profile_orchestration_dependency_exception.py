"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class LearnerProfileOrchestrationDependencyException(ApiError):
    """Wraps a dependency-tier failure raised by one of this service's four
    dependencies (LearnerProfile Processing, MistakePattern/TopicCovered/Flag
    Foundation).

    What lands here is LearnerProfileDependencyException,
    MistakePatternDependencyException, or TopicCoveredDependencyException --
    each already wrapping its own storage-failure leaf one level further in.
    FlagService.list_flags() raises nothing (a missing/corrupt flag file
    returns [] per its own contract), so there is no Flag-shaped leaf for
    this tier to catch.

    Mirrors ReviewOrchestrationDependencyException's shape
    (api/models/orchestrations/review/exceptions/review_orchestration_dependency_exception.py).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Learner profile orchestration dependency error occurred. Contact support.",
            inner_exception=inner_exception,
        )
