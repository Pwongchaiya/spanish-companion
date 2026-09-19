"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidPronunciationAssessmentRequestException(ApiError):
    """Raised by assess_pronunciation() when wav_bytes or reference_text fail a structural check.

    Batches every failing field into `errors` before raising, mirroring InvalidTtsRequestException
    (api/models/foundations/tts/exceptions/invalid_tts_request_exception.py).

    Leaf exception -- always wrapped into PronunciationAssessmentValidationException before leaving the service.
    """

    def __init__(self) -> None:
        super().__init__("Pronunciation assessment request is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
