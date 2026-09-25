"""ReviewOrchestrationService.explain_flag() -- F2: a still-weak grounding verdict
is recorded against the top retrieved chunk's RAE topic, best-effort."""

from rag.models.foundations.generation import FALLBACK_EXPLANATION, Explanation

WEAK = Explanation(explanation=FALLBACK_EXPLANATION, source_url="https://rae.example/1", source_excerpt="x")
GOOD = Explanation(explanation="grounded answer", source_url="https://rae.example/1", source_excerpt="x")


class TestReviewOrchestratorExplainFlagIngestionQueue:

    def test_should_record_weak_verdict_against_top_chunk_topic(
        self, service, mock_flag_service, mock_retrieval_service, mock_generation_service,
        mock_ingestion_queue_processing_service, make_flag, make_chunk, clock,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        top, other = make_chunk(1), make_chunk(2)
        top.topic, other.topic = "ser-vs-estar", "gender-agreement"
        mock_retrieval_service.retrieve.return_value = [top, other]
        mock_generation_service.explain.return_value = WEAK

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is WEAK
        mock_ingestion_queue_processing_service.record_weak_verdict.assert_called_once_with("ser-vs-estar", clock())

    def test_should_not_record_when_grounded(
        self, service, mock_flag_service, mock_retrieval_service, mock_generation_service,
        mock_ingestion_queue_processing_service, make_flag, make_chunk,
    ):
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = GOOD

        assert service.explain_flag("flag-1") is GOOD
        assert mock_ingestion_queue_processing_service.record_weak_verdict.call_count == 0

    def test_should_not_record_when_no_chunks_found(
        self, service, mock_flag_service, mock_retrieval_service, mock_ingestion_queue_processing_service, make_flag
    ):
        # no chunk -> no topic to attribute the failure to
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = []

        service.explain_flag("flag-1")

        assert mock_ingestion_queue_processing_service.record_weak_verdict.call_count == 0

    def test_should_return_same_explanation_and_not_raise_when_recording_fails(
        self, service, mock_flag_service, mock_retrieval_service, mock_generation_service,
        mock_ingestion_queue_processing_service, mock_logging_broker, make_flag, make_chunk,
    ):
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = WEAK
        mock_ingestion_queue_processing_service.record_weak_verdict.side_effect = RuntimeError("db down")

        actual = service.explain_flag("flag-1")

        assert actual is WEAK
        mock_ingestion_queue_processing_service.record_weak_verdict.assert_called_once()
        assert mock_logging_broker.log_info.call_count >= 1
