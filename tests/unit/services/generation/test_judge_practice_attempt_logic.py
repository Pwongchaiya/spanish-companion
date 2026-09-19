"""Unit tests for GenerationService.judge_practice_attempt().

A2 (graded practice-attempt verdict): one broker call, now returning one of
"again" | "hard" | "good" | "easy" instead of a binary YES/NO verdict.
"""

import pytest


class TestGenerationServiceJudgePracticeAttempt:

    @pytest.mark.parametrize("grade", ["again", "hard", "good", "easy"])
    def test_should_return_the_grade_word_when_broker_verdict_starts_with_it(
        self, service, mock_broker, flag, grade
    ):
        # given
        mock_broker.generate.return_value = f"{grade.upper()}, that's my assessment."

        # when
        result = service.judge_practice_attempt(flag, "yo tengo")

        # then
        assert result == grade

    def test_should_fall_back_to_again_when_broker_call_fails(self, service, mock_broker, flag):
        # given
        from rag.brokers.generation import GenerationError

        mock_broker.generate.side_effect = GenerationError("network blip")

        # when
        result = service.judge_practice_attempt(flag, "yo tengo")

        # then -- can't verify, so don't credit it
        assert result == "again"

    def test_should_fall_back_to_again_when_verdict_is_unparseable(self, service, mock_broker, flag):
        # given -- not one of the four known grade words
        mock_broker.generate.return_value = "definitely correct!"

        # when
        result = service.judge_practice_attempt(flag, "yo tengo")

        # then
        assert result == "again"

    def test_should_fall_back_to_again_when_verdict_is_blank(self, service, mock_broker, flag):
        # given
        mock_broker.generate.return_value = "   "

        # when
        result = service.judge_practice_attempt(flag, "yo tengo")

        # then
        assert result == "again"

    def test_should_include_original_mistake_and_attempt_text_in_prompt(self, service, mock_broker, flag):
        # given
        mock_broker.generate.return_value = "good"

        # when
        service.judge_practice_attempt(flag, "yo tengo")

        # then
        (prompt,), _ = mock_broker.generate.call_args
        assert flag.said in prompt
        assert flag.corrected in prompt
        assert flag.category in prompt
        assert "yo tengo" in prompt
