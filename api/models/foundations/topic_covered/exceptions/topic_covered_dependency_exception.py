"""Exposure-tier exception wrapping a broker-failure leaf exception."""

from api.errors import ApiError


class TopicCoveredDependencyException(ApiError):
    """Wraps TopicCoveredUnavailableError for consumers, without leaking
    internals. Mirrors LearnerProfileDependencyException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Topic covered data is currently unavailable. Try again shortly.",
            inner_exception,
        )
