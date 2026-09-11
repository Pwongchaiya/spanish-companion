"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidTopicCoveredException(ApiError):
    """Raised by create_topic_covered()/touch_topic_covered()/
    list_topic_covered_by_profile() when one or more arguments fail a
    structural check: profile_id/topic_id not a positive int, topic blank.

    Batches every failing field into `errors` before raising — reported
    together instead of raising on the first bad field. Mirrors
    NL.Core.Users' Xeption UpsertDataList/ThrowIfContainsErrors API exactly
    (UserProfileService.Validations.cs:252-269, confirmed used identically
    across all 9 of that project's *.Validations.cs files) — this is the
    verified source of truth, not a Python-idiom substitute. Renamed from
    InvalidTopicCoveredInputError (single-field, fail-fast) to match the
    MistakePattern rebuild's InvalidMistakePatternException naming — no
    "Input" infix, "Exception" not "Error".

    Leaf exception — always caught and wrapped into
    TopicCoveredValidationException before leaving TopicCoveredService.
    """

    def __init__(self) -> None:
        super().__init__("Topic covered is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
