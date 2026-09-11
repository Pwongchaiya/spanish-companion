"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidMistakePatternInputError(ApiError):
    """Raised by create()/update()/list_by_profile() when an argument fails
    a structural check: profile_id/pattern_id not a positive int, category
    blank, occurrence_count < 1, or status outside {"active", "resolved"}.

    Leaf exception -- always caught and wrapped into
    MistakePatternValidationException before leaving MistakePatternService,
    mirroring InvalidLearnerProfileInputError.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
