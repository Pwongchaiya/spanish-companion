"""Exposure-tier catch-all for anything the other two tiers didn't classify."""

from api.errors import ApiError


class PronunciationResultServiceException(ApiError):
    """Wraps any unexpected exception escaping PronunciationResultService."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Pronunciation result service error occurred, contact support.",
            inner_exception,
        )
