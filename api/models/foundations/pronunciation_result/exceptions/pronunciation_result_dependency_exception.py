"""Exposure-tier exception wrapping a dependency-tier leaf exception."""

from api.errors import ApiError


class PronunciationResultDependencyException(ApiError):
    """Wraps FailedPronunciationResultStorageException for consumers, without
    leaking the raw SQLAlchemy error."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation result dependency error occurred, contact support.",
            inner_exception,
        )
