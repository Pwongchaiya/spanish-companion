"""Leaf validation exception raised when a mistake-pattern row doesn't exist.

Not raised by any current MistakePatternService method (list_by_profile
returns an empty list rather than "not found"; create/update have no
missing-row read path) -- pinned now per CLAUDE.md's per-entity exception-
hierarchy waiver so Processing's record_occurrence()/resolve()
(find-by-category over list_by_profile's results) has it ready to raise
without a second entity round-trip. Renamed `<Condition><Entity>` per the
Flag/Session Lifecycle rebuild convention.
"""

from api.errors import ApiError


class NotFoundMistakePatternException(ApiError):
    """Raised when a lookup by id/category finds no matching row.

    Leaf exception -- always caught and wrapped into
    MistakePatternValidationException before leaving MistakePatternService.
    """

    def __init__(self) -> None:
        super().__init__("No mistake pattern exists for the given lookup")
