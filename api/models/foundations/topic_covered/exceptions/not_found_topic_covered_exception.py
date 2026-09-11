"""Leaf not-found exception for a topic_covered row.

Not raised anywhere in TopicCoveredService today -- this Foundation service
is pure CRUD over ITopicCoveredBroker's actual surface
(select_by_profile/insert/touch), which has no find-by-topic lookup to come
back empty. Defined here, in the shared model exceptions module, because
Processing's future find-by-topic step (part of `record_topic()`'s
upsert -- see Projects/spanish-companion/entities/topic-covered.md) will
raise it once built. Pinned now so the exception hierarchy name is fixed
before Processing needs it.
"""

from api.errors import ApiError


class NotFoundTopicCoveredException(ApiError):
    """Raised when a topic_covered row expected to exist can't be found."""

    def __init__(self) -> None:
        super().__init__("No topic_covered row exists for that lookup")
