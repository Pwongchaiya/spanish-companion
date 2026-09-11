"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class TopicCoveredValidationException(ApiError):
    """Wraps InvalidTopicCoveredException / NotFoundTopicCoveredException
    for consumers, without leaking internals. Mirrors
    MistakePatternValidationException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Topic covered validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
