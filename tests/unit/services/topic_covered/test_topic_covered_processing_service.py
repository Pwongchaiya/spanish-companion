"""Relocated from topic_covered_processing_service.py's __main__ self-check
-- production files don't carry test code, matching
NL.Core.Users.Api.Tests.Unit being a separate tree from NL.Core.Users.Api.
Both branches of the find-or-create decision (insert and touch/upsert) are
verified separately, matching MistakePatternProcessingService's test shape.
"""

from datetime import datetime
from unittest.mock import Mock

from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.processings.topic_covered.topic_covered_processing_service import (
    TopicCoveredProcessingService,
)


def test_topic_covered_processing_service():
    existing = TopicCovered(
        id=1, profile_id=1, topic="ser vs estar", first_covered_at=datetime(2026, 1, 1), last_practiced_at=datetime(2026, 1, 1)
    )

    # record_topic: found -> touch branch
    touched = TopicCovered(
        id=1, profile_id=1, topic="ser vs estar", first_covered_at=datetime(2026, 1, 1), last_practiced_at=datetime(2026, 9, 10)
    )
    foundation = Mock()
    foundation.list_topic_covered_by_profile.return_value = [existing]
    foundation.touch_topic_covered.return_value = touched
    service = TopicCoveredProcessingService(foundation)

    assert service.record_topic(1, "ser vs estar") is touched
    foundation.touch_topic_covered.assert_called_once_with(1)
    foundation.create_topic_covered.assert_not_called()

    # record_topic: not found -> insert branch
    created = TopicCovered(
        id=2, profile_id=1, topic="preterite", first_covered_at=datetime(2026, 9, 10), last_practiced_at=datetime(2026, 9, 10)
    )
    foundation = Mock()
    foundation.list_topic_covered_by_profile.return_value = [existing]
    foundation.create_topic_covered.return_value = created
    service = TopicCoveredProcessingService(foundation)

    assert service.record_topic(1, "preterite") is created
    foundation.create_topic_covered.assert_called_once_with(1, "preterite")
    foundation.touch_topic_covered.assert_not_called()
