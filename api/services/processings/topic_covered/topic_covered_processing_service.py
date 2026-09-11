"""Processing service for topic_covered.

Higher-order logic on top of the single Foundation dependency
(ITopicCoveredService): find-or-touch-or-create for a (profile_id, topic)
pair. Foundation stays pure CRUD (list_by_profile/create/touch, no
find-by-topic, no upsert) -- this is exactly the composition the Processing
tier exists for per CLAUDE.md's Processing-row reversal and the entity doc
(Projects/spanish-companion/entities/topic-covered.md).

One method -> no base/validations/exceptions mixin split (that split earns
its keep once there's more than one method to organise; see Foundation's
three-file layout for when it does).
"""

from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.foundations.topic_covered.i_topic_covered_service import ITopicCoveredService


class TopicCoveredProcessingService:
    """Combines Foundation's list_by_profile() + touch()/create() into a
    single find-or-create call. Do-or-delegate: this method decides which
    Foundation call to make, then delegates entirely -- it never transforms
    the result.
    """

    def __init__(self, topic_covered_service: ITopicCoveredService) -> None:
        self._topic_covered_service = topic_covered_service

    def record_topic(self, profile_id: int, topic: str) -> TopicCovered:
        existing = next(
            (row for row in self._topic_covered_service.list_by_profile(profile_id) if row.topic == topic),
            None,
        )
        if existing is not None:
            return self._topic_covered_service.touch(existing.id)
        return self._topic_covered_service.create(profile_id, topic)


if __name__ == "__main__":
    # ponytail: the one runnable check -- both branches of the
    # find-or-create decision, against a mocked Foundation service (per
    # test-processing-skill.md's "always mock Foundation" rule, done here as
    # a lightweight self-check since CLAUDE.md's "no tests during build"
    # waiver applies).
    from datetime import datetime
    from unittest.mock import Mock

    existing = TopicCovered(
        id=1, profile_id=1, topic="ser vs estar", first_covered_at=datetime(2026, 1, 1), last_practiced_at=datetime(2026, 1, 1)
    )
    touched = TopicCovered(
        id=1, profile_id=1, topic="ser vs estar", first_covered_at=datetime(2026, 1, 1), last_practiced_at=datetime(2026, 9, 10)
    )
    foundation = Mock()
    foundation.list_by_profile.return_value = [existing]
    foundation.touch.return_value = touched
    service = TopicCoveredProcessingService(foundation)

    assert service.record_topic(1, "ser vs estar") is touched
    foundation.touch.assert_called_once_with(1)
    foundation.create.assert_not_called()

    created = TopicCovered(
        id=2, profile_id=1, topic="preterite", first_covered_at=datetime(2026, 9, 10), last_practiced_at=datetime(2026, 9, 10)
    )
    foundation = Mock()
    foundation.list_by_profile.return_value = [existing]
    foundation.create.return_value = created
    service = TopicCoveredProcessingService(foundation)

    assert service.record_topic(1, "preterite") is created
    foundation.create.assert_called_once_with(1, "preterite")
    foundation.touch.assert_not_called()

    print("topic_covered_processing_service self-check passed")
