"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidSessionLogEntryException(ApiError):
    """Raised by create_session_log_entry()/complete_session_log_entry()
    when one or more arguments fail a structural check: entry_id not a
    positive int, started_at/ended_at not a datetime, flag_count negative
    or not an int, ended_at before started_at.

    Batches every failing field into `errors` before raising -- reported
    together instead of raising on the first bad field, mirroring
    NL.Core.Users' Xeption UpsertDataList/ThrowIfContainsErrors API
    (UserProfileService.Validations.cs:252-269) via the
    InvalidTopicCoveredException precedent in this codebase.

    Leaf exception -- always caught and wrapped into
    SessionLogEntryValidationException before leaving
    SessionLogEntryService.
    """

    def __init__(self) -> None:
        super().__init__("Session log entry is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
