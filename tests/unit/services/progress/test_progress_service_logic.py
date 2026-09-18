"""Unit tests for ProgressOrchestrationService's two read methods -- the
happy-path flow: ensure_profile composition, pass-through of
list_mistake_patterns_by_profile(), and the topic-coverage merge (dedupe
the corpus's (topic, url) pairs, mark each covered/not-covered against the
profile's TopicCovered rows).
"""

from unittest.mock import patch


class TestListMistakeSummary:

    def test_should_return_patterns_for_ensured_profile(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        make_profile,
        make_pattern,
    ):
        # given
        profile = make_profile(profile_id=7)
        mock_learner_profile_processing_service.ensure_profile.return_value = profile
        patterns = [make_pattern(pattern_id=1, category="ser_estar")]
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = patterns

        # when
        actual = service.list_mistake_summary()

        # then
        assert actual == patterns
        mock_learner_profile_processing_service.ensure_profile.assert_called_once_with("beginner")
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.assert_called_once_with(7)

    def test_should_return_empty_list_when_learner_has_no_patterns(
        self, service, mock_learner_profile_processing_service, mock_mistake_pattern_service, make_profile
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []

        # when
        actual = service.list_mistake_summary()

        # then
        assert actual == []

    def test_should_log_and_not_error_when_summary_succeeds(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_logging_broker,
        make_profile,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []

        # when
        service.list_mistake_summary()

        # then
        mock_logging_broker.log_info.assert_called_once()
        mock_logging_broker.log_error.assert_not_called()


FAKE_TOPICS = [
    ("ser-vs-estar", "url-1"),
    ("ser-vs-estar", "url-2"),  # duplicate topic, different URL -- must collapse to one entry
    ("subjunctive-basics", "url-3"),
]


class TestListTopicCoverage:

    def test_should_mark_topic_covered_with_first_covered_at_when_a_topic_covered_row_exists(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_topic_covered_service,
        make_profile,
        make_topic,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = [
            make_topic(topic_id=1, topic="ser-vs-estar")
        ]

        # when
        with patch("api.services.orchestrations.progress.progress_service.TOPICS", FAKE_TOPICS):
            actual = service.list_topic_coverage()

        # then -- duplicate (topic, url) pairs collapse to one entry, order preserved
        assert [e.topic for e in actual] == ["ser-vs-estar", "subjunctive-basics"]
        assert actual[0].covered is True
        assert actual[0].first_covered_at is not None
        assert actual[1].covered is False
        assert actual[1].first_covered_at is None

    def test_should_mark_every_topic_uncovered_when_learner_has_no_topic_covered_rows(
        self, service, mock_learner_profile_processing_service, mock_topic_covered_service, make_profile
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []

        # when
        with patch("api.services.orchestrations.progress.progress_service.TOPICS", FAKE_TOPICS):
            actual = service.list_topic_coverage()

        # then
        assert all(not e.covered and e.first_covered_at is None for e in actual)

    def test_should_log_and_not_error_when_coverage_succeeds(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_topic_covered_service,
        mock_logging_broker,
        make_profile,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_topic_covered_service.list_topic_covered_by_profile.return_value = []

        # when
        with patch("api.services.orchestrations.progress.progress_service.TOPICS", FAKE_TOPICS):
            service.list_topic_coverage()

        # then
        mock_logging_broker.log_info.assert_called_once()
        mock_logging_broker.log_error.assert_not_called()
