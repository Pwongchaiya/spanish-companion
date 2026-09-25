"""Unit tests for GenerationService.explain() -- GenerationError / not-grounded
fallback.

GenerationBroker.generate() failing, and the grounding judge (GAP 1,
Tri-Nature gap analysis) ruling the draft not grounded, both route through
the same fallback -- the service never lets an ungrounded or failed
explanation escape, and never invents a second fallback mechanism.
"""

from rag.brokers.generation import GenerationError
from rag.models.foundations.generation import FALLBACK_EXPLANATION, Explanation


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
            explanation=FALLBACK_EXPLANATION,
            source_url=chunk.source_url,
            source_excerpt=chunk.content,
        )
        mock_broker.generate.assert_called_once()

    def test_should_return_fallback_explanation_when_judge_rules_draft_not_grounded(
        self, service, mock_broker, flag, chunk
    ):
        # given
        mock_broker.generate.side_effect = [
            "The corrected form is right because reasons unrelated to the source.",
            "NO, the reference content does not support this claim.",
        ]

        # when
        result = service.explain(flag, chunk)

        # then
        assert result == Explanation(
            explanation=FALLBACK_EXPLANATION,
            source_url=chunk.source_url,
            source_excerpt=chunk.content,
        )
        assert mock_broker.generate.call_count == 2

    def test_should_log_judge_verdict_when_draft_not_grounded(
        self, service, mock_broker, mock_logging_broker, flag, chunk
    ):
        # given
        mock_broker.generate.side_effect = [
            "The corrected form is right because reasons unrelated to the source.",
            "NO, the reference content does not support this claim.",
        ]

        # when
        service.explain(flag, chunk)

        # then
        mock_logging_broker.log_info.assert_any_call(
            "grounding judge verdict: %s", "NO, the reference content does not support this claim."
        )

    def test_should_return_fallback_explanation_when_judge_call_itself_raises_generation_error(
        self, service, mock_broker, flag, chunk
    ):
        # given -- draft succeeds, but the judge call fails; can't verify
        # groundedness so it's treated as not grounded, same fallback.
        mock_broker.generate.side_effect = [
            "Great question! 'Tengo' is the correct form.",
            GenerationError("Gemini client call failed: boom"),
        ]

        # when
        result = service.explain(flag, chunk)

        # then
        assert result == Explanation(
            explanation=FALLBACK_EXPLANATION,
            source_url=chunk.source_url,
            source_excerpt=chunk.content,
        )
        assert mock_broker.generate.call_count == 2

    def test_should_mark_fallback_explanation_as_fallback(self, service, mock_broker, flag, chunk):
        # given
        mock_broker.generate.side_effect = GenerationError("Gemini client call failed: boom")

        # when
        result = service.explain(flag, chunk)

        # then
        assert result.is_fallback is True

    def test_should_not_mark_grounded_explanation_as_fallback(self, service, mock_broker, flag, chunk):
        # given
        mock_broker.generate.side_effect = [
            "Great question! 'Tengo' is the correct form.",
            "YES, the reference content supports this claim.",
        ]

        # when
        result = service.explain(flag, chunk)

        # then
        assert result.is_fallback is False
