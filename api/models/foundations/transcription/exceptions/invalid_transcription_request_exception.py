"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidTranscriptionRequestException(ApiError):
    """Raised by transcribe() when the uploaded audio fails a structural check (missing, empty,
    non-RIFF/WAVE), mirroring InvalidPronunciationAssessmentRequestException
    (api/models/foundations/pronunciation_assessment/exceptions/invalid_pronunciation_assessment_request_exception.py).

    Leaf exception -- always wrapped into TranscriptionValidationException before leaving the service.
    """

    def __init__(self) -> None:
        super().__init__("Transcription request is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
