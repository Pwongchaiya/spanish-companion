"""Unit tests for GenerationService.explain() -- happy path.

See test_explain_exceptions.py for the GenerationError fallback.
"""

from rag.models.generation import Explanation


class TestGenerationServiceExplain:

    def test_should_return_broker_text_and_chunk_source_url_when_generation_succeeds(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.return_value = "Great question! 'Tengo' is the correct form."

        # when
        result = service.explain(flag, chunk)

        # then
        assert result == Explanation(
            explanation="Great question! 'Tengo' is the correct form.",
            source_url=chunk.source_url,
        )
        mock_broker.generate.assert_called_once()

    def test_should_include_flag_and_chunk_details_in_prompt_passed_to_broker(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.return_value = "some explanation"

        # when
        service.explain(flag, chunk)

        # then
        mock_broker.generate.assert_called_once()
        (prompt,), _ = mock_broker.generate.call_args
        assert flag.said in prompt
        assert flag.corrected in prompt
        assert flag.category in prompt
        assert chunk.content in prompt
