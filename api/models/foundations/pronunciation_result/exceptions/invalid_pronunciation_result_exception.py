"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidPronunciationResultException(ApiError):
    """Raised by create_pronunciation_result() when one or more fields fail a
    structural check: reference_text/locale blank, a score not finite or
    outside 0..100, words_json not a list, created_at not a datetime.

    Batches every failing field into `errors` before raising, same
    UpsertDataList/ThrowIfContainsErrors shape as
    InvalidSessionLogEntryException.

    Leaf exception -- always caught and wrapped into
    PronunciationResultValidationException before leaving the service.
    """

    def __init__(self) -> None:
        super().__init__("Pronunciation result is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
