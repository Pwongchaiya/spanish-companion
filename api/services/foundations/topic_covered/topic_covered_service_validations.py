"""Validation checks for TopicCoveredService.

Mirrors NL.Core.Users' Validate(...)/Is* predicate-helper pattern
(NL.Core.Users.Api/Services/Foundations/UserProfiles/
UserProfileService.Validations.cs:19-41, 252-269) via the
MistakePatternServiceValidations precedent — each public method's checks
batch into one InvalidTopicCoveredException reporting every failing field,
instead of raising on the first bad field. Method names embed the entity
name (`_validate_topic_covered_on_create`, matching `ValidateUserProfileOnAdd`),
not just the verb.
"""

from api.models.foundations.topic_covered.exceptions import InvalidTopicCoveredException


class TopicCoveredServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input doesn't pass checks. See topic_covered_service_exceptions.py
    for how it gets wrapped and logged before leaving the service.
    """

    def _validate_topic_covered_on_list_by_profile(self, profile_id: int | None) -> None:
        self._validate(
            (self._is_invalid_id(profile_id), "profile_id", "Profile id is required"),
        )

    def _validate_topic_covered_on_create(self, profile_id: int | None, topic: str | None) -> None:
        self._validate(
            (self._is_invalid_id(profile_id), "profile_id", "Profile id is required"),
            (self._is_invalid_string(topic), "topic", "Topic is required"),
        )

    def _validate_topic_covered_on_touch(self, topic_id: int | None) -> None:
        self._validate(
            (self._is_invalid_id(topic_id), "topic_id", "Topic id is required"),
        )

    @staticmethod
    def _is_invalid_id(value: int | None) -> bool:
        return value is None or value <= 0

    @staticmethod
    def _is_invalid_string(value: str | None) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidTopicCoveredException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
