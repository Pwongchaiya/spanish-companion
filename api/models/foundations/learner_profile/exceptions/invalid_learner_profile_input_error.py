"""Leaf validation exception raised when proficiency_level fails input checks."""

from api.errors import ApiError


class InvalidLearnerProfileInputError(ApiError):
    """Raised by create_profile()/update_proficiency_level() when
    proficiency_level is None or an empty/whitespace-only string.

    No CEFR enum constraint exists yet -- the entity doc
    (Projects/spanish-companion/entities/learner-profile.md) types the field
    as `str | None` with no declared value set, so this only rejects
    missing/blank input, not out-of-range values. Tighten to an enum check
    here if/when the doc pins one.

    Leaf exception -- always caught and wrapped into
    LearnerProfileValidationException before leaving LearnerProfileService,
    mirroring NotFoundFlagException -> FlagValidationException.
    """

    def __init__(self, proficiency_level: str | None) -> None:
        super().__init__(f"Invalid proficiency_level: {proficiency_level!r}")
