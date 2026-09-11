"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class LearnerProfileValidationException(ApiError):
    """Wraps InvalidLearnerProfileException / NotFoundLearnerProfileException
    for consumers, without leaking internals. Mirrors FlagValidationException's
    shape -- both leaves land here, so no consumer-side discrimination beyond
    the message is required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Learner profile validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
