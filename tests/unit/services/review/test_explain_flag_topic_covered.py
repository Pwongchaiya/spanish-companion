"""ReviewOrchestrationService.explain_flag() -- F1 follow-up: a grounded
(non-fallback) explanation records the top retrieved chunk's topic against
the learner's profile, best-effort, so Progress's corpus-coverage map
reflects real explain activity instead of staying permanently empty."""

from rag.models.foundations.generation import FALLBACK_EXPLANATION, Explanation

WEAK = Explanation(explanation=FALLBACK_EXPLANATION, source_url="https://rae.example/1", source_excerpt="x")
GOOD = Explanation(explanation="grounded answer", source_url="https://rae.example/1", source_excerpt="x")


class TestReviewOrchestratorExplainFlagTopicCovered:

    def test_should_record_top_chunk_topic_when_explanation_is_grounded(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        mock_learner_profile_processing_service,
        mock_topic_covered_processing_service,
        make_flag,
        make_chunk,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        top, other = make_chunk(1), make_chunk(2)
        top.topic, other.topic = "ser-vs-estar", "gender-agreement"
        mock_retrieval_service.retrieve.return_value = [top, other]
        mock_generation_service.explain.return_value = GOOD

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is GOOD
        profile = mock_learner_profile_processing_service.ensure_profile.return_value
        mock_topic_covered_processing_service.record_topic.assert_called_once_with(profile.id, "ser-vs-estar")

    def test_should_not_record_when_explanation_is_fallback(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        mock_topic_covered_processing_service,
        make_flag,
        make_chunk,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = WEAK

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is WEAK
        assert mock_topic_covered_processing_service.record_topic.call_count == 0

    def test_should_not_record_when_no_chunks_found(
        self, service, mock_flag_service, mock_retrieval_service, mock_topic_covered_processing_service, make_flag
    ):
        # no chunk -> no topic to attribute the explanation to
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = []

        service.explain_flag("flag-1")

        assert mock_topic_covered_processing_service.record_topic.call_count == 0

    def test_should_return_same_explanation_and_not_raise_when_recording_fails(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        mock_topic_covered_processing_service,
        mock_logging_broker,
        make_flag,
        make_chunk,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = GOOD
        mock_topic_covered_processing_service.record_topic.side_effect = RuntimeError("db down")

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is GOOD
        mock_topic_covered_processing_service.record_topic.assert_called_once()
        assert mock_logging_broker.log_info.call_count >= 1
