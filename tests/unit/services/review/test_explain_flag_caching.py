"""Unit test for ReviewOrchestrator.explain_flag()'s lru_cache.

Flags are immutable once created and the corpus is static, so a repeat call
with the same flag_id must not re-hit retrieval/generation. See the
`ponytail:` comment on explain_flag() in review_service.py.
"""


class TestReviewOrchestratorExplainFlagCaching:

    def test_should_call_generation_only_once_for_repeated_calls_with_same_flag_id(
        self,
        service,
        mock_flag_service,
        mock_retrieval_service,
        mock_generation_service,
        make_flag,
        make_chunk,
    ):
        # given
        flag = make_flag("flag-3", corrected="fui al mercado", category="preterite")
        mock_flag_service.get_flag.return_value = flag
        mock_retrieval_service.retrieve.return_value = [make_chunk(chunk_id=20, score=0.8)]

        # when
        first = service.explain_flag("flag-3")
        second = service.explain_flag("flag-3")

        # then
        assert first is second
        mock_generation_service.explain.assert_called_once()
        mock_flag_service.get_flag.assert_called_once_with("flag-3")
        mock_retrieval_service.retrieve.assert_called_once()
