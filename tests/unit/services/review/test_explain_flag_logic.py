"""Unit tests for ReviewOrchestrator.explain_flag() -- happy path and the
no-corpus-match fallback.

See test_explain_flag_exceptions.py for the unknown-flag_id refusal.

RETRIEVAL_TOP_K is asserted by reference to the module constant, never as a
literal 3 -- it is read from env at import time, and hardcoding the default
would make these tests silently disagree with the service.
"""

from rag.models.generation import Explanation

from api.services.review import RETRIEVAL_TOP_K


class TestReviewOrchestratorExplainFlag:

    def test_should_explain_top_ranked_chunk_when_retrieval_returns_results(
        self,
        service,
        mock_flag_broker,
        mock_retrieval_controller,
        mock_generation_controller,
        make_flag,
        make_chunk,
    ):
        # given
        flag = make_flag("flag-2", corrected="fui al mercado", category="preterite")
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1"), flag]

        top_chunk = make_chunk(chunk_id=10, score=0.91)
        runner_up = make_chunk(chunk_id=11, score=0.42)
        mock_retrieval_controller.retrieve.return_value = [top_chunk, runner_up]

        expected = Explanation(explanation="grounded answer", source_url=top_chunk.source_url)
        mock_generation_controller.explain.return_value = expected

        # when
        actual = service.explain_flag("flag-2")

        # then
        assert actual is expected
        mock_flag_broker.load_flags.assert_called_once_with()
        mock_retrieval_controller.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        # chunks[0] specifically -- retrieve() returns best-first.
        mock_generation_controller.explain.assert_called_once_with(flag, top_chunk)

    def test_should_return_fallback_without_calling_generation_when_retrieval_is_empty(
        self,
        service,
        mock_flag_broker,
        mock_retrieval_controller,
        mock_generation_controller,
        make_flag,
    ):
        # given
        flag = make_flag("flag-1", corrected="fui al mercado", category="preterite")
        mock_flag_broker.load_flags.return_value = [flag]
        mock_retrieval_controller.retrieve.return_value = []

        # when
        actual = service.explain_flag("flag-1")

        # then
        assert actual == Explanation(explanation="I'm not certain on that one.", source_url="")
        mock_flag_broker.load_flags.assert_called_once_with()
        mock_retrieval_controller.retrieve.assert_called_once_with(
            query="fui al mercado",
            top_k=RETRIEVAL_TOP_K,
            category="preterite",
        )
        mock_generation_controller.explain.assert_not_called()
