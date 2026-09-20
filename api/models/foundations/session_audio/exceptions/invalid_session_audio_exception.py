"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidSessionAudioException(ApiError):
    """Batches every failing field into `errors` before raising. Leaf exception --
    always wrapped into SessionAudioValidationException before leaving the service."""

    def __init__(self) -> None:
        super().__init__("Session audio is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
