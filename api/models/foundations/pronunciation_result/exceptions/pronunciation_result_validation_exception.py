"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class PronunciationResultValidationException(ApiError):
    """Wraps InvalidPronunciationResultException for consumers."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation result validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
