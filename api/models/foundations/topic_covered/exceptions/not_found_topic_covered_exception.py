"""Leaf validation exception raised when a topic_covered row doesn't exist.

Raised by TopicCoveredService.touch_topic_covered() when the broker returns
None for a missing topic_id (broker's None-on-missing-id convention, same
as select_topic_covered_by_profile() returning an empty list for no rows —
Foundation checks for None and raises this directly, mirroring
MistakePatternService.update_mistake_pattern()'s
NotFoundMistakePatternException path). list_topic_covered_by_profile()
itself still returns an empty list rather than raising — "no rows for this
profile" isn't a not-found condition.
"""

from api.errors import ApiError


class NotFoundTopicCoveredException(ApiError):
    """Raised when a lookup by id finds no matching topic_covered row.

    Leaf exception — always caught and wrapped into
    TopicCoveredValidationException before leaving TopicCoveredService.
    """

    def __init__(self) -> None:
        super().__init__("No topic_covered row exists for that lookup")
