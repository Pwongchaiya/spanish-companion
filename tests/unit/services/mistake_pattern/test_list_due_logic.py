"""list_due(): filter to next_due_at <= now (not None), ordered ascending."""

from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import Mock

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.processings.mistake_pattern.mistake_pattern_processing_service import (
    MistakePatternProcessingService,
)

NOW = datetime(2026, 9, 19, 12, 0, 0)


def _pattern(pattern_id: int, next_due_at: Optional[datetime]) -> MistakePattern:
    return MistakePattern(
        id=pattern_id,
        profile_id=1,
        category=f"cat-{pattern_id}",
        occurrence_count=1,
        last_seen_at=NOW,
        status="active",
        next_due_at=next_due_at,
    )


class TestMistakePatternProcessingServiceListDue:

    def test_should_return_only_due_patterns_ordered_by_next_due_at_ascending(self):
        # given
        later = _pattern(1, NOW - timedelta(hours=1))
        earliest = _pattern(2, NOW - timedelta(days=3))
        exactly_now = _pattern(3, NOW)
        future = _pattern(4, NOW + timedelta(seconds=1))
        unscheduled = _pattern(5, None)
        foundation = Mock(spec=IMistakePatternService)
        foundation.list_mistake_patterns_by_profile.return_value = [later, future, unscheduled, exactly_now, earliest]
        service = MistakePatternProcessingService(foundation)

        # when
        actual = service.list_due(1, NOW)

        # then
        assert actual == [earliest, later, exactly_now]
        foundation.list_mistake_patterns_by_profile.assert_called_once_with(1)

    def test_should_return_empty_list_when_nothing_is_due(self):
        # given
        foundation = Mock(spec=IMistakePatternService)
        foundation.list_mistake_patterns_by_profile.return_value = [_pattern(1, None)]
        service = MistakePatternProcessingService(foundation)

        # when / then
        assert service.list_due(1, NOW) == []
