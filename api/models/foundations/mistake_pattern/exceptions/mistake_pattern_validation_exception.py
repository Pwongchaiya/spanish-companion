"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class MistakePatternValidationException(ApiError):
    """Wraps InvalidMistakePatternInputError / NotFoundMistakePatternException
    for consumers, without leaking internals. Mirrors
    LearnerProfileValidationException's shape.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Mistake pattern validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
