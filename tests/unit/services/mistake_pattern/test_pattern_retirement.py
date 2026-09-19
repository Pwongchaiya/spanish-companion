"""A8: retired = resolved and interval_days >= 30.0 (derived); list_due hides it, record_occurrence resurfaces it."""

from datetime import datetime, timedelta
from unittest.mock import Mock

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.processings.mistake_pattern.mistake_pattern_processing_service import (
    MistakePatternProcessingService,
)

NOW = datetime(2026, 9, 19, 12, 0, 0)


def _pattern(status: str, interval_days: float) -> MistakePattern:
    return MistakePattern(
        id=7,
        profile_id=1,
        category="ser vs estar",
        occurrence_count=3,
        last_seen_at=NOW,
        status=status,
        interval_days=interval_days,
        next_due_at=NOW - timedelta(days=1),
    )


def _service(rows, clock=lambda: NOW):
    foundation = Mock(spec=IMistakePatternService)
    foundation.list_mistake_patterns_by_profile.return_value = rows
    return foundation, MistakePatternProcessingService(foundation, clock=clock)


class TestPatternRetirement:

    def test_should_drop_resolved_row_from_list_due_after_easy_review_crosses_30_days(self):
        # given
        foundation, service = _service([_pattern("resolved", 10.0)])
        foundation.update_mistake_pattern.side_effect = lambda _id, **kw: MistakePattern(
            id=7, profile_id=1, category="ser vs estar", occurrence_count=3, last_seen_at=NOW,
            status="resolved", interval_days=kw["interval_days"], next_due_at=NOW - timedelta(days=1),
        )
        reviewed = service.record_review(1, "ser vs estar", "easy")
        assert reviewed.interval_days == 35.0
        foundation.list_mistake_patterns_by_profile.return_value = [reviewed]

        # when / then
        assert service.list_due(1, NOW) == []

    def test_should_still_list_resolved_row_below_30_days(self):
        row = _pattern("resolved", 29.0)
        _, service = _service([row])
        assert service.list_due(1, NOW) == [row]

    def test_should_still_list_active_row_with_large_interval(self):
        row = _pattern("active", 90.0)
        _, service = _service([row])
        assert service.list_due(1, NOW) == [row]

    def test_should_resurface_retired_row_on_recurrence(self):
        # given
        foundation, service = _service([_pattern("resolved", 30.0)])

        # when
        service.record_occurrence(1, "ser vs estar")

        # then
        foundation.update_mistake_pattern.assert_called_once_with(
            7, occurrence_count=4, status="active", interval_days=1.0, next_due_at=NOW
        )

    def test_should_leave_interval_untouched_on_recurrence_of_non_retired_row(self):
        # given
        foundation, service = _service([_pattern("resolved", 29.0)])

        # when
        service.record_occurrence(1, "ser vs estar")

        # then
        foundation.update_mistake_pattern.assert_called_once_with(7, occurrence_count=4, status="active")
