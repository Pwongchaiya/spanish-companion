"""Processing service for topic_covered.

Higher-order logic on top of the single Foundation dependency
(ITopicCoveredService): find-by-topic (over
list_topic_covered_by_profile's results) composed with
insert-or-touch. Foundation stays pure CRUD (see
topic_covered_service.py's docstring) -- this is exactly the composition
the Processing tier exists for per CLAUDE.md's Processing-row reversal and
the entity doc (Projects/spanish-companion/entities/topic-covered.md).

One method, do-or-delegate: it decides which Foundation call to make from
the find-by-topic result, then delegates entirely -- it never transforms a
Foundation response afterward. No base/validations/exceptions mixin split
(that split earns its keep once there's per-method noise to organise; see
Foundation's three-file layout for when it does -- same call made for
MistakePatternProcessingService).
"""

from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.foundations.topic_covered.i_topic_covered_service import ITopicCoveredService


class TopicCoveredProcessingService:
    """Find-by-topic over Foundation's list_topic_covered_by_profile(),
    then delegates to create_topic_covered/touch_topic_covered.
    """

    def __init__(self, topic_covered_service: ITopicCoveredService) -> None:
        self._topic_covered_service = topic_covered_service

    def record_topic(self, profile_id: int, topic: str) -> TopicCovered:
        existing = self._find_by_topic(profile_id, topic)
        if existing is None:
            return self._topic_covered_service.create_topic_covered(profile_id, topic)
        return self._topic_covered_service.touch_topic_covered(existing.id)

    def _find_by_topic(self, profile_id: int, topic: str) -> TopicCovered | None:
        rows = self._topic_covered_service.list_topic_covered_by_profile(profile_id)
        return next((row for row in rows if row.topic == topic), None)
