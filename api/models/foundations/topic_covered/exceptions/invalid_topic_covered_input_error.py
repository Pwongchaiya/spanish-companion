"""Leaf validation exception raised when `topic` fails input checks."""

from api.errors import ApiError


class InvalidTopicCoveredInputError(ApiError):
    """Raised by TopicCoveredService.create() when `topic` is None or an
    empty/whitespace-only string.

    Leaf exception -- always caught and wrapped into
    TopicCoveredValidationException before leaving TopicCoveredService,
    mirroring InvalidLearnerProfileInputError -> LearnerProfileValidationException.
    """

    def __init__(self, topic: str | None) -> None:
        super().__init__(f"Invalid topic: {topic!r}")
