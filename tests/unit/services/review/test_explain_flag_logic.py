"""Unit tests for ReviewOrchestrationService.explain_flag() -- happy path and the
no-corpus-match fallback.

See test_explain_flag_exceptions.py for the unknown-flag_id refusal.

RETRIEVAL_TOP_K is asserted by reference to conftest's constant, never as a
bare literal 3 -- it is the same value the `configuration_broker` fixture
feeds the service, so tests and service can't silently drift apart.

#64: Review passes GenerationService.explain() the FULL retrieved chunk
list now, not just chunks[0] -- GenerationService itself decides how many
of them (EXPLAIN_TOP_K) to ground on. That slicing is GenerationService's
own unit-tested behaviour (tests/unit/services/generation/); this suite
only asserts Review hands over the whole list.
"""

from rag.models.foundations.generation import FALLBACK_EXPLANATION, Explanation

from tests.unit.services.review.conftest import RETRIEVAL_TOP_K


class TestReviewOrchestratorExplainFlag:

    def test_should_explain_top_ranked_chunk_when_retrieval_returns_results(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        make_flag,
        make_chunk,
    ):
        # given
        flag = make_flag("flag-2", corrected="fui al mercado", category="preterite")
        mock_flag_service.get_flag.return_value = flag

        top_chunk = make_chunk(chunk_id=10, score=0.91)
        runner_up = make_chunk(chunk_id=11, score=0.42)
        mock_retrieval_service.retrieve.return_value = [top_chunk, runner_up]

        expected = Explanation(
            explanation="grounded answer", source_url=top_chunk.source_url, source_excerpt=top_chunk.content
        )
        mock_generation_service.explain.return_value = expected

        # when
        actual = service.explain_flag("flag-2")

        # then
        assert actual is expected
        mock_flag_service.get_flag.assert_called_once_with("flag-2")
        mock_retrieval_service.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        # #64: the full retrieved (best-first) list, not just chunks[0].
        mock_generation_service.explain.assert_called_once_with(flag, [top_chunk, runner_up])

    def test_should_return_fallback_without_calling_generation_when_retrieval_is_empty(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        make_flag,
    ):
        # given
        flag = make_flag("flag-1", corrected="fui al mercado", category="preterite")
        mock_flag_service.get_flag.return_value = flag
        mock_retrieval_service.retrieve.return_value = []

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual == Explanation(explanation=FALLBACK_EXPLANATION, source_url="", source_excerpt="")
        mock_flag_service.get_flag.assert_called_once_with("flag-1")
        mock_retrieval_service.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        mock_generation_service.explain.assert_not_called()
