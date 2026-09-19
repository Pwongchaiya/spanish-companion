"""Foundation update_mistake_pattern(): interval_days validation + scheduling passthrough."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.mistake_pattern.i_mistake_pattern_broker import IMistakePatternBroker
from api.models.foundations.mistake_pattern.exceptions import MistakePatternValidationException
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.services.foundations.mistake_pattern import MistakePatternService

DUE = datetime(2026, 9, 20, 12, 0, 0)


class TestMistakePatternServiceUpdateScheduling:

    @pytest.mark.parametrize("bad_interval", [0, -1.5])
    def test_should_reject_non_positive_interval_days_without_calling_broker(self, bad_interval):
        # given
        broker = Mock(spec=IMistakePatternBroker)
        service = MistakePatternService(broker, logging_broker=Mock())

        # when / then
        with pytest.raises(MistakePatternValidationException):
            service.update_mistake_pattern(1, 1, "active", bad_interval, DUE)

        broker.update_mistake_pattern.assert_not_called()

    def test_should_forward_scheduling_fields_to_broker(self):
        # given
        broker = Mock(spec=IMistakePatternBroker)
        updated = MistakePattern(
            id=1, profile_id=1, category="c", occurrence_count=1, last_seen_at=DUE, status="active",
            interval_days=2.0, next_due_at=DUE,
        )
        broker.update_mistake_pattern.return_value = updated
        service = MistakePatternService(broker, logging_broker=Mock())

        # when
        actual = service.update_mistake_pattern(1, 1, "active", 2.0, DUE)

        # then
        assert actual is updated
        broker.update_mistake_pattern.assert_called_once_with(1, 1, "active", 2.0, DUE)
