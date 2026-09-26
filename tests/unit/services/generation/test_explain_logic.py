"""Unit tests for GenerationService.explain() -- happy path.

Two broker.generate() calls now happen per explain(): the draft explanation,
then the grounding judge call (GAP 1, Tri-Nature gap analysis). See
test_explain_exceptions.py for the GenerationError / not-grounded fallback,
and test_explain_top_k_logic.py for #64's EXPLAIN_TOP_K slicing behaviour.
"""

from rag.models.foundations.generation import Explanation


class TestGenerationServiceExplain:

    def test_should_return_broker_text_and_top_chunk_source_url_when_generation_succeeds_and_grounded(
        self, service, mock_broker, flag, chunk, chunks
    ):
        # given -- `chunk` is chunks[0] (top-ranked); source_url/source_excerpt
        # always reflect it, even though both chunks fed the prompt.
        mock_broker.generate.side_effect = [
            "Great question! 'Tengo' is the correct form.",
            "YES, the reference content confirms this.",
        ]

        # when
        result = service.explain(flag, chunks)

        # then
        assert result == Explanation(
            explanation="Great question! 'Tengo' is the correct form.",
            source_url=chunk.source_url,
            source_excerpt=chunk.content,
        )
        assert mock_broker.generate.call_count == 2

    def test_should_include_flag_and_all_chunk_contents_in_draft_prompt_passed_to_broker(
        self, service, mock_broker, flag, chunk, other_chunk, chunks
    ):
        # given
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        service.explain(flag, chunks)

        # then
        assert mock_broker.generate.call_count == 2
        (draft_prompt,), _ = mock_broker.generate.call_args_list[0]
        assert flag.said in draft_prompt
        assert flag.corrected in draft_prompt
        assert flag.category in draft_prompt
        assert chunk.content in draft_prompt
        assert other_chunk.content in draft_prompt

    def test_should_include_draft_explanation_and_all_chunk_contents_in_judge_prompt(
        self, service, mock_broker, flag, chunk, other_chunk, chunks
    ):
        # given
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        service.explain(flag, chunks)

        # then
        (judge_prompt,), _ = mock_broker.generate.call_args_list[1]
        assert "some explanation" in judge_prompt
        assert chunk.content in judge_prompt
        assert other_chunk.content in judge_prompt
