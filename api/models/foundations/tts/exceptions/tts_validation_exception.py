"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class TtsValidationException(ApiError):
    """Wraps InvalidTtsRequestException for consumers, without leaking
    internals.

    Mirrors TopicCoveredValidationException's shape
    (api/models/foundations/topic_covered/exceptions/
    topic_covered_validation_exception.py) -- only one leaf lands here, so
    no consumer-side discrimination is required.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Tts validation error occurred. Fix the errors and try again.", inner_exception)
