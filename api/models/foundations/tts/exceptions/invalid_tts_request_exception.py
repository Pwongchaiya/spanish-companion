"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidTtsRequestException(ApiError):
    """Raised by synthesize_speech() when `text` fails a structural check:
    blank/missing, or over the length cap.

    Batches every failing field into `errors` before raising, mirroring
    InvalidTopicCoveredException's UpsertDataList/ThrowIfContainsErrors
    shape (api/models/foundations/topic_covered/exceptions/
    invalid_topic_covered_exception.py) -- same project convention, only
    one field to check here.

    Leaf exception -- always caught and wrapped into TtsValidationException
    before leaving TtsService.
    """

    def __init__(self) -> None:
        super().__init__("Tts request is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
