"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidMistakePatternException(ApiError):
    """Raised by create()/update()/list_by_profile() when one or more
    arguments fail a structural check: profile_id/pattern_id not a positive
    int, category blank, occurrence_count < 1, or status outside
    {"active", "resolved"}.

    Batches every failing field into `errors` before raising -- reported
    together instead of raising on the first bad field. Mirrors
    NL.Core.Users' Xeption UpsertDataList/ThrowIfContainsErrors API exactly
    (UserProfileService.Validations.cs:252-269, confirmed used identically
    across all 9 of that project's *.Validations.cs files) -- this is the
    verified source of truth, not a Python-idiom substitute. Named to match
    InvalidUserProfileException -- no "Input" infix, "Exception" not "Error".

    Leaf exception -- always caught and wrapped into
    MistakePatternValidationException before leaving MistakePatternService.
    """

    def __init__(self) -> None:
        super().__init__("Mistake pattern is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
