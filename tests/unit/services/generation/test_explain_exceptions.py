"""Unit tests for GenerationService.explain() -- GenerationError fallback.

GenerationBroker.generate() is the only failure mode this feature has (per
CLAUDE.md's Foundation waiver for Generation: no 9-class exception
hierarchy, just GenerationError). The service catches it and substitutes
Phase 1's exact fallback string -- it never lets GenerationError escape.
"""

from rag.brokers.generation import GenerationError
from rag.models.generation import Explanation


class TestGenerationServiceExplainExceptions:

    def test_should_return_fallback_explanation_when_broker_raises_generation_error(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.side_effect = GenerationError("Gemini client call failed: boom")

        # when
        result = service.explain(flag, chunk)

        # then
        assert result == Explanation(
            explanation="I'm not certain on that one.",
            source_url=chunk.source_url,
        )
        mock_broker.generate.assert_called_once()
