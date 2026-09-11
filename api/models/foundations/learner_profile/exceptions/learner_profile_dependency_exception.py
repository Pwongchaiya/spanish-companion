"""Exposure-tier exception wrapping a broker-failure leaf exception."""

from api.errors import ApiError


class LearnerProfileDependencyException(ApiError):
    """Wraps FailedLearnerProfileStorageException for consumers, without leaking
    internals. Mirrors FlagDependencyException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Learner profile is currently unavailable. Try again shortly.",
            inner_exception,
        )
