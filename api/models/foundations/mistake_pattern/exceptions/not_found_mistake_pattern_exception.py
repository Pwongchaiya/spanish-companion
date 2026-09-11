"""Leaf validation exception raised when a mistake-pattern row doesn't exist.

Raised by two independent callers, for two different lookups:
Processing's resolve() (find-by-category over list_by_profile's results,
no DB round-trip) and Foundation's update() (broker returns None when
pattern_id doesn't exist -- same convention as select_by_profile()
returning an empty list for no rows; Foundation checks for None and raises
this directly, mirroring LearnerProfileService._get_profile()).
list_by_profile() itself still returns an empty list rather than raising --
"no rows for this profile" isn't a not-found condition. Renamed
`<Condition><Entity>` per the Flag/Session Lifecycle rebuild convention.
"""

from api.errors import ApiError


class NotFoundMistakePatternException(ApiError):
    """Raised when a lookup by id/category finds no matching row.

    Leaf exception -- always caught and wrapped into
    MistakePatternValidationException before leaving MistakePatternService.
    """

    def __init__(self) -> None:
        super().__init__("No mistake pattern exists for the given lookup")
