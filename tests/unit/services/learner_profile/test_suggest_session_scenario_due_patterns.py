"""A3 priming brief: suggest_session_scenario() maps list_due() rows to DuePattern."""

from datetime import timedelta

import pytest

from api.models.orchestrations.learner_profile.session_scenario import DuePattern
from tests.unit.services.learner_profile.conftest import FIXED_NOW


@pytest.fixture(autouse=True)
def _quiet_dependencies(
    mock_learner_profile_processing_service,
    mock_mistake_pattern_service,
    mock_topic_covered_service,
    mock_flag_service,
    make_profile,
):
    mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=7)
    mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
    mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
    mock_flag_service.list_flags.return_value = []


def _due(make_pattern, i, category, days_ago, occurrences=1):
    p = make_pattern(i, category=category, occurrence_count=occurrences)
    p.next_due_at = FIXED_NOW - timedelta(days=days_ago)
    return p


class TestSuggestSessionScenarioDuePatterns:

    def test_should_map_due_rows_in_order_and_call_list_due_once_with_profile_id_and_clock(
        self, service, mock_mistake_pattern_processing_service, make_pattern
    ):
        mock_mistake_pattern_processing_service.list_due.return_value = [
            _due(make_pattern, 1, "gender", 3, occurrences=4),
            _due(make_pattern, 2, "ser_estar", -0.5, occurrences=2),  # not overdue yet -> clamped to 0
        ]

        actual = service.suggest_session_scenario()

        assert actual.due_patterns == [DuePattern("gender", 4, 3.0), DuePattern("ser_estar", 2, 0.0)]
        mock_mistake_pattern_processing_service.list_due.assert_called_once_with(7, FIXED_NOW)

    def test_should_cap_due_list_at_configured_limit(
        self, service, mock_mistake_pattern_processing_service, make_pattern, configuration_broker
    ):
        mock_mistake_pattern_processing_service.list_due.return_value = [
            _due(make_pattern, i, f"c{i}", 5 - i) for i in range(5)
        ]

        assert [d.category for d in service.suggest_session_scenario().due_patterns] == ["c0", "c1", "c2"]

        configuration_broker._values["DUE_BRIEF_LIMIT"] = "1"
        assert [d.category for d in service.suggest_session_scenario().due_patterns] == ["c0"]

    @pytest.mark.parametrize("bad", ["abc", "-1", ""])
    def test_should_fall_back_to_default_limit_on_bad_config(
        self, service, mock_mistake_pattern_processing_service, make_pattern, configuration_broker, bad
    ):
        mock_mistake_pattern_processing_service.list_due.return_value = [
            _due(make_pattern, i, f"c{i}", 5 - i) for i in range(5)
        ]
        configuration_broker._values["DUE_BRIEF_LIMIT"] = bad

        assert len(service.suggest_session_scenario().due_patterns) == 3

    def test_should_return_empty_due_patterns_when_nothing_due(self, service, mock_mistake_pattern_processing_service):
        mock_mistake_pattern_processing_service.list_due.return_value = []

        assert service.suggest_session_scenario().due_patterns == []
