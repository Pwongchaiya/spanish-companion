"""Exposure-tier exception wrapping a broker-failure leaf exception."""

from api.errors import ApiError


class MistakePatternDependencyException(ApiError):
    """Wraps FailedMistakePatternStorageException for consumers, without leaking
    internals. Mirrors LearnerProfileDependencyException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Mistake pattern data is currently unavailable. Try again shortly.",
            inner_exception,
        )
