"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidLearnerProfileException(ApiError):
    """Raised by create_learner_profile()/update_learner_profile() when one
    or more arguments fail a structural check: profile_id not a positive
    int (update only), or proficiency_level blank/None.

    Batches every failing field into `errors` before raising -- reported
    together instead of raising on the first bad field. Mirrors
    NL.Core.Users' Xeption UpsertDataList/ThrowIfContainsErrors API exactly
    (UserProfileService.Validations.cs:252-269) -- same convention already
    applied to InvalidMistakePatternException. Named to match
    InvalidUserProfileException -- no "Input" infix, "Exception" not "Error".

    Leaf exception -- always caught and wrapped into
    LearnerProfileValidationException before leaving LearnerProfileService.
    """

    def __init__(self) -> None:
        super().__init__("Learner profile is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
