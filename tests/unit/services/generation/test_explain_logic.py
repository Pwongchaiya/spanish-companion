"""Unit tests for GenerationService.explain() -- happy path.

Two broker.generate() calls now happen per explain(): the draft explanation,
then the grounding judge call (GAP 1, Tri-Nature gap analysis). See
test_explain_exceptions.py for the GenerationError / not-grounded fallback.
"""

from rag.models.generation import Explanation


class TestGenerationServiceExplain:

    def test_should_return_broker_text_and_chunk_source_url_when_generation_succeeds_and_grounded(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.side_effect = [
            "Great question! 'Tengo' is the correct form.",
            "YES, the reference content confirms this.",
        ]

        # when
        result = service.explain(flag, chunk)

        # then
        assert result == Explanation(
            explanation="Great question! 'Tengo' is the correct form.",
            source_url=chunk.source_url,
        )
        assert mock_broker.generate.call_count == 2

    def test_should_include_flag_and_chunk_details_in_draft_prompt_passed_to_broker(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        service.explain(flag, chunk)

        # then
        assert mock_broker.generate.call_count == 2
        (draft_prompt,), _ = mock_broker.generate.call_args_list[0]
        assert flag.said in draft_prompt
        assert flag.corrected in draft_prompt
        assert flag.category in draft_prompt
        assert chunk.content in draft_prompt

    def test_should_include_draft_explanation_and_chunk_content_in_judge_prompt(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        service.explain(flag, chunk)

        # then
        (judge_prompt,), _ = mock_broker.generate.call_args_list[1]
        assert "some explanation" in judge_prompt
        assert chunk.content in judge_prompt
