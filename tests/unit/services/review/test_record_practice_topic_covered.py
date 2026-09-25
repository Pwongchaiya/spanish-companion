"""ReviewOrchestrationService.record_practice() -- F1 follow-up: a mastered
attempt (grade "good"/"easy") maps its flag's category to a corpus topic via
category_matches_topic() (rag/services/orchestrations/retrieval/strategies/
filters.py) and records it, best-effort, mirroring the mistake_pattern write
this method already makes on the same mastered branch.
"""


class TestReviewOrchestratorRecordPracticeTopicCovered:

    def test_should_record_matched_topic_when_judge_says_mastered(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_learner_profile_processing_service,
        mock_topic_covered_processing_service,
        make_flag,
    ):
        # given -- "ser_estar" grounds to the corpus topic "ser-vs-estar" via
        # category_matches_topic's normalization (underscores/hyphens/"vs"
        # all collapse to the same word-boundary comparison).
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = "good"

        # when
        result = service.record_practice("flag-1", "estoy cansado")

        # then
        assert result.mastered is True
        profile = mock_learner_profile_processing_service.ensure_profile.return_value
        mock_topic_covered_processing_service.record_topic.assert_called_once_with(profile.id, "ser-vs-estar")

    def test_should_record_matched_topic_when_judge_says_easy(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_learner_profile_processing_service,
        mock_topic_covered_processing_service,
        make_flag,
    ):
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = "easy"

        result = service.record_practice("flag-1", "estoy cansado")

        assert result.mastered is True
        profile = mock_learner_profile_processing_service.ensure_profile.return_value
        mock_topic_covered_processing_service.record_topic.assert_called_once_with(profile.id, "ser-vs-estar")

    def test_should_not_record_when_judge_says_still_shaky(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_topic_covered_processing_service,
        make_flag,
    ):
        # given -- "again"/"hard" never reach the mastered branch at all
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = "again"

        result = service.record_practice("flag-1", "soy cansado")

        assert result.mastered is False
        assert mock_topic_covered_processing_service.record_topic.call_count == 0

    def test_should_not_record_when_category_matches_no_corpus_topic(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_topic_covered_processing_service,
        make_flag,
    ):
        # given -- "vocabulary" is a deliberately uncovered category (see
        # rag/data/topics.py's docstring): mastered, but nothing to record.
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="vocabulary")
        mock_generation_service.judge_practice_attempt.return_value = "good"

        result = service.record_practice("flag-1", "la manzana")

        assert result.mastered is True
        assert mock_topic_covered_processing_service.record_topic.call_count == 0

    def test_should_not_raise_when_recording_fails(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_topic_covered_processing_service,
        mock_logging_broker,
        make_flag,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = "good"
        mock_topic_covered_processing_service.record_topic.side_effect = RuntimeError("db down")

        # when
        result = service.record_practice("flag-1", "estoy cansado")

        # then
        assert result.mastered is True
        mock_topic_covered_processing_service.record_topic.assert_called_once()
        assert mock_logging_broker.log_info.call_count >= 1
