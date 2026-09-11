"""Validation checks for MistakePatternService.

Mirrors NL.Core.Users' Validate(...)/Is* predicate-helper pattern
(NL.Core.Users.Api/Services/Foundations/UserProfiles/
UserProfileService.Validations.cs:19-41, 252-269) -- each public method's
checks batch into one InvalidMistakePatternException reporting every
failing field, instead of raising on the first bad field. Method names
embed the entity name (`_validate_mistake_pattern_on_create`, matching
`ValidateUserProfileOnAdd`), not just the verb.
"""

from api.models.foundations.mistake_pattern.exceptions import InvalidMistakePatternException

_VALID_STATUSES = {"active", "resolved"}


class MistakePatternServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input doesn't pass checks. See mistake_pattern_service_exceptions.py
    for how it gets wrapped and logged before leaving the service.
    """

    def _validate_mistake_pattern_on_list_by_profile(self, profile_id: int | None) -> None:
        self._validate(
            (self._is_invalid_id(profile_id), "profile_id", "Profile id is required"),
        )

    def _validate_mistake_pattern_on_create(self, profile_id: int | None, category: str | None) -> None:
        self._validate(
            (self._is_invalid_id(profile_id), "profile_id", "Profile id is required"),
            (self._is_invalid_string(category), "category", "Category is required"),
        )

    def _validate_mistake_pattern_on_update(
        self, pattern_id: int | None, occurrence_count: int | None, status: str | None
    ) -> None:
        self._validate(
            (self._is_invalid_id(pattern_id), "pattern_id", "Pattern id is required"),
            (self._is_invalid_occurrence_count(occurrence_count), "occurrence_count", "Occurrence count must be at least 1"),
            (status not in _VALID_STATUSES, "status", "Status is not recognized"),
        )

    @staticmethod
    def _is_invalid_id(value: int | None) -> bool:
        return value is None or value <= 0

    @staticmethod
    def _is_invalid_string(value: str | None) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_invalid_occurrence_count(value: int | None) -> bool:
        return value is None or value < 1

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidMistakePatternException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
