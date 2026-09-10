"""Unit tests for ReviewOrchestrator.explain_flag() -- happy path and the
no-corpus-match fallback.

See test_explain_flag_exceptions.py for the unknown-flag_id refusal.

RETRIEVAL_TOP_K is asserted by reference to conftest's constant, never as a
bare literal 3 -- it is the same value the `configuration_broker` fixture
feeds the service, so tests and service can't silently drift apart.
"""

from rag.models.generation import Explanation

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

        expected = Explanation(explanation="grounded answer", source_url=top_chunk.source_url)
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
        # chunks[0] specifically -- retrieve() returns best-first.
        mock_generation_service.explain.assert_called_once_with(flag, top_chunk)

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
        assert actual == Explanation(explanation="I'm not certain on that one.", source_url="")
        mock_flag_service.get_flag.assert_called_once_with("flag-1")
        mock_retrieval_service.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        mock_generation_service.explain.assert_not_called()
