"""record_review(): grade -> interval multiplier + next_due_at from the injected clock."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern.i_mistake_pattern_service import IMistakePatternService
from api.services.processings.mistake_pattern.mistake_pattern_processing_service import (
    MistakePatternProcessingService,
)

NOW = datetime(2026, 9, 19, 12, 0, 0)


def _pattern(interval_days: float = 2.0) -> MistakePattern:
    return MistakePattern(
        id=7,
        profile_id=1,
        category="ser vs estar",
        occurrence_count=3,
        last_seen_at=NOW,
        status="active",
        interval_days=interval_days,
    )


class TestMistakePatternProcessingServiceRecordReview:

    @pytest.mark.parametrize(
        "grade,expected_interval",
        [("again", 1.0), ("hard", 2.4), ("good", 4.0), ("easy", 7.0)],
    )
    def test_should_update_interval_and_due_date_by_grade(self, grade, expected_interval):
        # given
        foundation = Mock(spec=IMistakePatternService)
        foundation.list_mistake_patterns_by_profile.return_value = [_pattern(2.0)]
        updated = _pattern(expected_interval)
        foundation.update_mistake_pattern.return_value = updated
        service = MistakePatternProcessingService(foundation, clock=lambda: NOW)

        # when
        actual = service.record_review(1, "ser vs estar", grade)

        # then
        assert actual is updated
        foundation.list_mistake_patterns_by_profile.assert_called_once_with(1)
        foundation.update_mistake_pattern.assert_called_once_with(
            7,
            occurrence_count=3,
            status="active",
            interval_days=pytest.approx(expected_interval),
            next_due_at=NOW + timedelta(days=expected_interval),
        )
        foundation.create_mistake_pattern.assert_not_called()

    def test_should_reset_interval_to_one_day_on_again_regardless_of_prior_interval(self):
        # given
        foundation = Mock(spec=IMistakePatternService)
        foundation.list_mistake_patterns_by_profile.return_value = [_pattern(30.0)]
        service = MistakePatternProcessingService(foundation, clock=lambda: NOW)

        # when
        service.record_review(1, "ser vs estar", "again")

        # then
        assert foundation.update_mistake_pattern.call_args.kwargs["interval_days"] == 1.0
