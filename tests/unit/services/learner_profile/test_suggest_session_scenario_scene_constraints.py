"""A4: suggest_session_scenario() emits one hard scene constraint per capped due pattern."""

from datetime import timedelta

import pytest

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


def _due(make_pattern, i, category):
    p = make_pattern(i, category=category, occurrence_count=1)
    p.next_due_at = FIXED_NOW - timedelta(days=1)
    return p


class TestSuggestSessionScenarioSceneConstraints:

    def test_should_emit_one_constraint_per_due_pattern_capped_at_default_two(
        self, service, mock_mistake_pattern_processing_service, make_pattern
    ):
        mock_mistake_pattern_processing_service.list_due.return_value = [
            _due(make_pattern, i, c) for i, c in enumerate(["ser_estar", "gender", "preterite"])
        ]

        actual = service.suggest_session_scenario()

        assert actual.scene_constraints == [
            "The scene must force me to use ser estar to get through it.",
            "The scene must force me to use gender to get through it.",
        ]
        assert len(actual.due_patterns) == 3
        mock_mistake_pattern_processing_service.list_due.assert_called_once_with(7, FIXED_NOW)

    @pytest.mark.parametrize("value,expected", [("1", 1), ("0", 0), ("abc", 2), ("-1", 2)])
    def test_should_honor_configured_limit_and_fall_back_on_bad_value(
        self, service, mock_mistake_pattern_processing_service, make_pattern, configuration_broker, value, expected
    ):
        mock_mistake_pattern_processing_service.list_due.return_value = [
            _due(make_pattern, i, f"c{i}") for i in range(3)
        ]
        configuration_broker._values["SCENE_CONSTRAINT_LIMIT"] = value

        assert len(service.suggest_session_scenario().scene_constraints) == expected

    def test_should_return_no_constraints_when_nothing_due(self, service, mock_mistake_pattern_processing_service):
        mock_mistake_pattern_processing_service.list_due.return_value = []

        assert service.suggest_session_scenario().scene_constraints == []
