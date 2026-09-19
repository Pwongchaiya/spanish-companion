"""Validation checks for SessionLogEntryService.

Mirrors NL.Core.Users' Validate(...)/Is* predicate-helper pattern
(NL.Core.Users.Api/Services/Foundations/UserProfiles/
UserProfileService.Validations.cs:19-41, 252-269) via the
TopicCoveredServiceValidations precedent -- each public method's checks
batch into one InvalidSessionLogEntryException reporting every failing
field, instead of raising on the first bad field. Method names embed the
entity name (`_validate_session_log_entry_on_create`, matching
`ValidateUserProfileOnAdd`), not just the verb.

list_session_log_entries() takes no input, so it has no validator here --
same as Review's no-input reads.
"""

from datetime import datetime

from api.models.foundations.session_log_entry.exceptions import InvalidSessionLogEntryException


class SessionLogEntryServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input does not pass checks. See
    session_log_entry_service_exceptions.py for how it gets wrapped and
    logged before leaving the service.
    """

    def _validate_session_log_entry_on_create(self, started_at: datetime | None) -> None:
        self._validate(
            (self._is_invalid_datetime(started_at), "started_at", "Started at is required"),
        )

    def _validate_session_log_entry_on_complete(
        self, entry_id: int | None, ended_at: datetime | None, flag_count: int | None
    ) -> None:
        self._validate(
            (self._is_invalid_id(entry_id), "entry_id", "Entry id is required"),
            (self._is_invalid_datetime(ended_at), "ended_at", "Ended at is required"),
            (self._is_invalid_count(flag_count), "flag_count", "Flag count must be zero or more"),
        )

    @staticmethod
    def _is_invalid_id(value: int | None) -> bool:
        # bool is an int subclass in Python, so True would otherwise pass
        # as entry_id=1 -- excluded explicitly here and in _is_invalid_count.
        return not isinstance(value, int) or isinstance(value, bool) or value <= 0

    @staticmethod
    def _is_invalid_count(value: int | None) -> bool:
        return not isinstance(value, int) or isinstance(value, bool) or value < 0

    @staticmethod
    def _is_invalid_datetime(value: datetime | None) -> bool:
        return not isinstance(value, datetime)

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidSessionLogEntryException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
