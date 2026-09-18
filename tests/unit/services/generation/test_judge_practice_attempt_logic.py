"""Unit tests for GenerationService.judge_practice_attempt().

LearnerProfile Phase 2 (see decisions/dynamic-bot-behavior-and-learner-memory.md).
Same shape as explain()'s grounding judge: one broker call, YES/NO verdict.
"""


class TestGenerationServiceJudgePracticeAttempt:

    def test_should_return_true_when_broker_verdict_starts_with_yes(self, service, mock_broker, flag):
        # given
        mock_broker.generate.return_value = "YES, that's the correct preterite form."

        # when
        result = service.judge_practice_attempt(flag, "yo tengo")

        # then
        assert result is True

    def test_should_return_false_when_broker_verdict_starts_with_no(self, service, mock_broker, flag):
        # given
        mock_broker.generate.return_value = "NO, that's still incorrect."

        # when
        result = service.judge_practice_attempt(flag, "yo soy tener")

        # then
        assert result is False

    def test_should_return_false_when_broker_call_fails(self, service, mock_broker, flag):
        # given
        from rag.brokers.generation import GenerationError

        mock_broker.generate.side_effect = GenerationError("network blip")

        # when
        result = service.judge_practice_attempt(flag, "yo tengo")

        # then -- can't verify, so don't credit it
        assert result is False

    def test_should_include_original_mistake_and_attempt_text_in_prompt(self, service, mock_broker, flag):
        # given
        mock_broker.generate.return_value = "YES"

        # when
        service.judge_practice_attempt(flag, "yo tengo")

        # then
        (prompt,), _ = mock_broker.generate.call_args
        assert flag.said in prompt
        assert flag.corrected in prompt
        assert flag.category in prompt
        assert "yo tengo" in prompt
