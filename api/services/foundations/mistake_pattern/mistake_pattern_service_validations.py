"""Validation checks for MistakePatternService.

Mirrors LearnerProfileServiceValidations's shape -- private methods
containing a single `if (condition): raise LeafException()` check, called
from the base service file's public-method bodies rather than inlined
there.
"""

from api.models.foundations.mistake_pattern.exceptions import InvalidMistakePatternInputError

_VALID_STATUSES = {"active", "resolved"}


class MistakePatternServiceValidations:
    """Mixin: raises the leaf exceptions when input doesn't pass checks.
    See mistake_pattern_service_exceptions.py for how these get wrapped and
    logged before leaving the service.
    """

    def _validate_profile_id(self, profile_id: int | None) -> None:
        if profile_id is None or profile_id <= 0:
            raise InvalidMistakePatternInputError(f"Invalid profile_id: {profile_id!r}")

    def _validate_category(self, category: str | None) -> None:
        if category is None or not category.strip():
            raise InvalidMistakePatternInputError(f"Invalid category: {category!r}")

    def _validate_pattern_id(self, pattern_id: int | None) -> None:
        if pattern_id is None or pattern_id <= 0:
            raise InvalidMistakePatternInputError(f"Invalid pattern_id: {pattern_id!r}")

    def _validate_occurrence_count(self, occurrence_count: int | None) -> None:
        if occurrence_count is None or occurrence_count < 1:
            raise InvalidMistakePatternInputError(f"Invalid occurrence_count: {occurrence_count!r}")

    def _validate_status(self, status: str | None) -> None:
        if status not in _VALID_STATUSES:
            raise InvalidMistakePatternInputError(f"Invalid status: {status!r}")
