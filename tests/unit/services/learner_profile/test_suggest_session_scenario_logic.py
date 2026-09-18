"""Unit tests for LearnerProfileOrchestrationService.suggest_session_scenario()
-- the happy-path flow control branches: focus_category selection (active-only,
highest occurrence_count), suggested_topic fallback (focus_category first, else
oldest-practiced topic), recent_mistake_categories (config-limited, deduped,
newest-first), and the default-level fallback when the profile has no level yet.
"""

from datetime import datetime

from api.models.orchestrations.learner_profile.session_scenario import SessionScenario


class TestSuggestSessionScenarioLogic:

    def test_should_pick_highest_occurrence_active_pattern_as_focus_when_multiple_active_patterns_exist(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
        make_pattern,
    ):
        # given
        profile = make_profile(profile_id=7, proficiency_level="intermediate")
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = [
            make_pattern(pattern_id=1, category="gender", occurrence_count=2, status="active"),
            make_pattern(pattern_id=2, category="ser_estar", occurrence_count=5, status="active"),
        ]
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.suggest_session_scenario()

        # then
        assert actual == SessionScenario(
            proficiency_level="intermediate",
            focus_category="ser_estar",
            suggested_topic="ser_estar",
            recent_mistake_categories=[],
        )
        mock_learner_profile_processing_service.ensure_profile.assert_called_once_with("beginner")
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.assert_called_once_with(7)
        mock_topic_covered_service.list_topic_covered_by_profile.assert_called_once_with(7)
        mock_flag_service.list_flags.assert_called_once_with()

    def test_should_ignore_resolved_patterns_when_picking_focus_category(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
        make_pattern,
    ):
        # given
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = [
            make_pattern(pattern_id=1, category="ser_estar", occurrence_count=9, status="resolved"),
        ]
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.suggest_session_scenario()

        # then
        assert actual.focus_category is None
        assert actual.suggested_topic is None

    def test_should_fall_back_to_oldest_practiced_topic_when_no_active_pattern_exists(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
        make_topic,
    ):
        # given
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = [
            make_topic(topic_id=1, topic="past_tense", last_practiced_at=datetime(2026, 9, 1)),
            make_topic(topic_id=2, topic="subjunctive", last_practiced_at=datetime(2026, 1, 2)),
        ]
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.suggest_session_scenario()

        # then
        assert actual.focus_category is None
        assert actual.suggested_topic == "subjunctive"

    def test_should_prefer_focus_category_over_due_topic_when_both_are_available(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
        make_pattern,
        make_topic,
    ):
        # given
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = [
            make_pattern(pattern_id=1, category="gender", occurrence_count=1, status="active"),
        ]
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = [
            make_topic(topic_id=1, topic="past_tense", last_practiced_at=datetime(2026, 1, 1)),
        ]
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.suggest_session_scenario()

        # then
        assert actual.suggested_topic == "gender"

    def test_should_return_none_scenario_fields_when_learner_has_no_history(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
    ):
        # given
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.suggest_session_scenario()

        # then
        assert actual.focus_category is None
        assert actual.suggested_topic is None
        assert actual.recent_mistake_categories == []

    def test_should_use_config_default_level_when_profile_has_no_level_yet(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
    ):
        # given
        profile = make_profile(profile_id=1, proficiency_level=None)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.suggest_session_scenario()

        # then
        assert actual.proficiency_level == "beginner"

    def test_should_use_configured_default_level_key_when_calling_ensure_profile(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        configuration_broker,
        make_profile,
    ):
        # given
        configuration_broker._values["DEFAULT_PROFICIENCY_LEVEL"] = "advanced"
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

        # when
        service.suggest_session_scenario()

        # then
        mock_learner_profile_processing_service.ensure_profile.assert_called_once_with("advanced")

    def test_should_dedupe_and_order_newest_first_when_recent_flags_share_categories(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        make_profile,
        make_flag,
    ):
        # given
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = [
            make_flag("flag-1", category="gender", timestamp=datetime(2026, 1, 1)),
            make_flag("flag-2", category="ser_estar", timestamp=datetime(2026, 1, 3)),
            make_flag("flag-3", category="gender", timestamp=datetime(2026, 1, 2)),
        ]

        # when
        actual = service.suggest_session_scenario()

        # then -- newest first (flag-2, flag-3, flag-1), gender deduped to its first (newest) occurrence
        assert actual.recent_mistake_categories == ["ser_estar", "gender"]

    def test_should_limit_recent_mistake_categories_to_configured_flag_limit(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        configuration_broker,
        make_profile,
        make_flag,
    ):
        # given
        configuration_broker._values["RECENT_FLAG_LIMIT"] = "2"
        profile = make_profile(profile_id=1)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = [
            make_flag("flag-1", category="gender", timestamp=datetime(2026, 1, 1)),
            make_flag("flag-2", category="ser_estar", timestamp=datetime(2026, 1, 2)),
            make_flag("flag-3", category="subjunctive", timestamp=datetime(2026, 1, 3)),
        ]

        # when
        actual = service.suggest_session_scenario()

        # then -- newest two only (flag-3, flag-2); flag-1's "gender" never considered
        assert actual.recent_mistake_categories == ["subjunctive", "ser_estar"]

    def test_should_log_scenario_summary_when_suggestion_succeeds(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        mock_logging_broker,
        make_profile,
    ):
        # given
        profile = make_profile(profile_id=1, proficiency_level="beginner")
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []
        mock_flag_service.list_flags.return_value = []

        # when
        service.suggest_session_scenario()

        # then
        mock_logging_broker.log_info.assert_called_once()
        mock_logging_broker.log_error.assert_not_called()
