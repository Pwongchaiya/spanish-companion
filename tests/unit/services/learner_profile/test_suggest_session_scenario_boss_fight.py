"""C4 boss fight: eligibility, ordering/cap, and text length."""

from datetime import timedelta

import pytest

from api.services.orchestrations.learner_profile.learner_profile_orchestration_service import (
    LearnerProfileOrchestrationService as Svc,
)
from tests.unit.services.learner_profile.conftest import FIXED_NOW


@pytest.fixture
def boss(make_pattern):
    def _make(i=1, category="gender", count=4, status="active", due=True, interval=1.0):
        p = make_pattern(i, category=category, occurrence_count=count, status=status)
        p.next_due_at = FIXED_NOW - timedelta(days=1) if due else FIXED_NOW + timedelta(days=1)
        p.interval_days = interval
        return p

    return _make


class TestPickBossPatterns:
    def test_should_pick_eligible_pattern(self, boss):
        p = boss()
        assert Svc._pick_boss_patterns([p], FIXED_NOW, 3) == [p]

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"status": "resolved"},
            {"due": False},
            {"count": 2},
            {"interval": 2.0},
            {"interval": 3.5},
        ],
    )
    def test_should_skip_ineligible_condition(self, boss, kwargs):
        assert Svc._pick_boss_patterns([boss(**kwargs)], FIXED_NOW, 3) == []

    def test_should_skip_pattern_never_scheduled(self, make_pattern):
        assert Svc._pick_boss_patterns([make_pattern(1, occurrence_count=5)], FIXED_NOW, 3) == []

    @pytest.mark.parametrize("kwargs", [{"count": 3}, {"interval": 1.99}])
    def test_should_include_at_boundary(self, boss, kwargs):
        p = boss(**kwargs)
        assert Svc._pick_boss_patterns([p], FIXED_NOW, 3) == [p]

    def test_should_order_by_occurrences_desc_and_cap_at_three(self, boss):
        ps = [boss(i, f"c{i}", count=3 + i) for i in range(5)]
        assert [p.category for p in Svc._pick_boss_patterns(ps, FIXED_NOW, 3)] == ["c4", "c3", "c2"]


class TestBossFightText:
    def test_should_fit_in_80_chars_and_drop_overflow(self):
        text, kept = Svc._boss_fight_text(
            ["a_long_category_name_one", "a_long_category_name_two", "a_long_category_name_3"]
        )
        assert len(text) <= 80
        assert kept == ["a_long_category_name_one", "a_long_category_name_two"]
        assert "one" in text and "3" not in text

    def test_should_return_empty_for_no_categories(self):
        assert Svc._boss_fight_text([]) == ("", [])


class TestSuggestScenarioBossFight:
    @pytest.fixture(autouse=True)
    def _deps(
        self, mock_learner_profile_processing_service, mock_topic_covered_service, mock_flag_service, make_profile
    ):
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=7)
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

    def test_should_fill_boss_fields(self, service, mock_mistake_pattern_service, boss):
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = [boss(1, "ser_estar")]
        actual = service.suggest_session_scenario()
        assert actual.boss_fight_text == "Boss fight: quiz me on ser estar"
        assert actual.boss_fight_categories == ["ser_estar"]
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.assert_called_once_with(7)

    def test_should_default_to_none_and_empty(self, service, mock_mistake_pattern_service):
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        actual = service.suggest_session_scenario()
        assert actual.boss_fight_text is None
        assert actual.boss_fight_categories == []
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.assert_called_once_with(7)
