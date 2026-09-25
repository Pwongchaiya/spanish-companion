"""Unit tests for ReviewOrchestrationService.explain_flag() -- F4 second-opinion pass.

A weak grounding verdict (Generation's fixed fallback string) triggers exactly
one lexical re-retrieve + regenerate, only when SECOND_OPINION_ENABLED=true.
Any failure of that pass degrades to the original explanation.
"""

import pytest

from api.services.orchestrations.review import ReviewOrchestrationService
from rag.models.foundations.generation import FALLBACK_EXPLANATION, Explanation
from tests.unit.services.review.conftest import RETRIEVAL_TOP_K, FakeConfigurationBroker

WEAK = Explanation(explanation=FALLBACK_EXPLANATION, source_url="https://rae.example/1", source_excerpt="x")
GOOD = Explanation(explanation="grounded answer", source_url="https://rae.example/2", source_excerpt="y")


@pytest.fixture
def enabled_service(
    mock_flag_service,
    mock_practice_log_service,
    mock_retrieval_service,
    mock_generation_service,
    mock_learner_profile_processing_service,
    mock_mistake_pattern_processing_service,
    mock_session_log_entry_service,
    mock_live_transcript_service,
    mock_ingestion_queue_processing_service,
    mock_topic_covered_processing_service,
    clock,
    mock_logging_broker,
):
    return ReviewOrchestrationService(
        flag_service=mock_flag_service,
        practice_log_service=mock_practice_log_service,
        retrieval_service=mock_retrieval_service,
        generation_service=mock_generation_service,
        learner_profile_processing_service=mock_learner_profile_processing_service,
        mistake_pattern_processing_service=mock_mistake_pattern_processing_service,
        session_log_entry_service=mock_session_log_entry_service,
        live_transcript_service=mock_live_transcript_service,
        ingestion_queue_processing_service=mock_ingestion_queue_processing_service,
        topic_covered_processing_service=mock_topic_covered_processing_service,
        clock=clock,
        configuration_broker=FakeConfigurationBroker(
            {"RETRIEVAL_TOP_K": str(RETRIEVAL_TOP_K), "SECOND_OPINION_ENABLED": "true"}
        ),
        logging_broker=mock_logging_broker,
    )


class TestReviewOrchestratorExplainFlagSecondOpinion:

    def test_should_regenerate_from_alternate_chunk_when_first_verdict_is_weak(
        self, enabled_service, mock_flag_service, mock_retrieval_service, mock_generation_service, make_flag, make_chunk
    ):
        # given
        flag = make_flag()
        mock_flag_service.get_flag.return_value = flag
        dense, lexical = make_chunk(1), make_chunk(2)
        mock_retrieval_service.retrieve.side_effect = [[dense], [lexical]]
        mock_generation_service.explain.side_effect = [WEAK, GOOD]

        # when
        actual = enabled_service.explain_flag("flag-1")

        # then
        assert actual is GOOD
        assert mock_retrieval_service.retrieve.call_count == 2
        second_call = mock_retrieval_service.retrieve.call_args_list[1]
        assert second_call.kwargs == {
            "query": flag.corrected,
            "top_k": RETRIEVAL_TOP_K,
            "category": flag.category,
            "alternate": True,
        }
        assert mock_generation_service.explain.call_count == 2
        mock_generation_service.explain.assert_called_with(flag, lexical)

    def test_should_not_retry_when_first_verdict_is_grounded(
        self, enabled_service, mock_flag_service, mock_retrieval_service, mock_generation_service, make_flag, make_chunk
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = GOOD

        # when
        actual = enabled_service.explain_flag("flag-1")

        # then
        assert actual is GOOD
        mock_retrieval_service.retrieve.assert_called_once()
        mock_generation_service.explain.assert_called_once()

    def test_should_not_retry_when_disabled(
        self, service, mock_flag_service, mock_retrieval_service, mock_generation_service, make_flag, make_chunk
    ):
        # given -- default fixture config has no SECOND_OPINION_ENABLED
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = WEAK

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual is WEAK
        mock_retrieval_service.retrieve.assert_called_once()
        mock_generation_service.explain.assert_called_once()

    def test_should_keep_original_when_second_pass_is_also_weak_and_cap_at_one_retry(
        self, enabled_service, mock_flag_service, mock_retrieval_service, mock_generation_service, make_flag, make_chunk
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.return_value = [make_chunk(1)]
        mock_generation_service.explain.return_value = WEAK

        # when
        actual = enabled_service.explain_flag("flag-1")

        # then
        assert actual is WEAK
        assert mock_retrieval_service.retrieve.call_count == 2
        assert mock_generation_service.explain.call_count == 2

    def test_should_keep_original_when_alternate_retrieval_finds_nothing(
        self, enabled_service, mock_flag_service, mock_retrieval_service, mock_generation_service, make_flag, make_chunk
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.side_effect = [[make_chunk(1)], []]
        mock_generation_service.explain.return_value = WEAK

        # when
        actual = enabled_service.explain_flag("flag-1")

        # then
        assert actual is WEAK
        assert mock_retrieval_service.retrieve.call_count == 2
        mock_generation_service.explain.assert_called_once()

    def test_should_keep_original_when_second_pass_raises(
        self, enabled_service, mock_flag_service, mock_retrieval_service, mock_generation_service, make_flag, make_chunk
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag()
        mock_retrieval_service.retrieve.side_effect = [[make_chunk(1)], RuntimeError("db down")]
        mock_generation_service.explain.return_value = WEAK

        # when
        actual = enabled_service.explain_flag("flag-1")

        # then -- degraded, not raised
        assert actual is WEAK
        assert mock_retrieval_service.retrieve.call_count == 2
        mock_generation_service.explain.assert_called_once()
