"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class ProgressOrchestrationValidationException(ApiError):
    """Wraps a Foundation/Processing-tier validation exception for
    consumers, without leaking internals.

    What lands here is LearnerProfileValidationException,
    MistakePatternValidationException, or TopicCoveredValidationException --
    the wrapper the service beneath raises, carried through whole rather
    than unwrapped. The leaf is therefore two levels deep, at
    `.inner_exception.inner_exception`.

    Mirrors LearnerProfileOrchestrationValidationException's shape
    (api/models/orchestrations/learner_profile/exceptions/learner_profile_orchestration_validation_exception.py).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Progress orchestration validation error occurred. Fix the errors and try again.",
            inner_exception=inner_exception,
        )
