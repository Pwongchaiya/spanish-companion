"""Validation checks for LearnerProfileService.

Mirrors NL.Core.Users' Validate(...)/Is* predicate-helper pattern
(NL.Core.Users.Api/Services/Foundations/UserProfiles/
UserProfileService.Validations.cs:19-41, 252-269) -- each public method's
checks batch into one InvalidLearnerProfileException reporting every
failing field, instead of raising on the first bad field. Method names
embed the entity name (`_validate_learner_profile_on_create`, matching
`ValidateUserProfileOnAdd`), same convention already applied to
MistakePatternServiceValidations.
"""

from api.models.foundations.learner_profile.exceptions import InvalidLearnerProfileException


class LearnerProfileServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input doesn't pass checks. See learner_profile_service_exceptions.py
    for how it gets wrapped and logged before leaving the service.
    """

    def _validate_learner_profile_on_create(self, proficiency_level: str | None) -> None:
        self._validate(
            (self._is_invalid_string(proficiency_level), "proficiency_level", "Proficiency level is required"),
        )

    def _validate_learner_profile_on_update(self, profile_id: int | None, proficiency_level: str | None) -> None:
        self._validate(
            (self._is_invalid_id(profile_id), "profile_id", "Profile id is required"),
            (self._is_invalid_string(proficiency_level), "proficiency_level", "Proficiency level is required"),
        )

    @staticmethod
    def _is_invalid_id(value: int | None) -> bool:
        return value is None or value <= 0

    @staticmethod
    def _is_invalid_string(value: str | None) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidLearnerProfileException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
