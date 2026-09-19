"""Unit tests for GenerationService.judge_task_outcome() -- roadmap D4.

Same swallow-to-None shape as estimate_cefr_level(): a broker failure or an
unparseable verdict returns None (leave unjudged), never a guessed outcome.
"""

import pytest

from rag.brokers.generation import GenerationError


class TestGenerationServiceJudgeTaskOutcome:

    @pytest.mark.parametrize(
        "verdict, expected",
        [("SUCCESS, ordered both.", "success"), ("success", "success"), ("FAIL. never ordered food", "fail"), ("Fail", "fail")],
    )
    def test_should_parse_first_word_of_verdict(self, service, mock_broker, verdict, expected):
        # given
        mock_broker.generate.return_value = verdict

        # when
        result = service.judge_task_outcome("[user] un cafe", "orders a drink")

        # then
        assert result == expected
        assert mock_broker.generate.call_count == 1

    def test_should_return_none_when_verdict_is_unparseable(self, service, mock_broker):
        # given
        mock_broker.generate.return_value = "Hard to say."

        # when / then
        assert service.judge_task_outcome("transcript", "cond") is None

    def test_should_return_none_when_broker_call_fails(self, service, mock_broker):
        # given
        mock_broker.generate.side_effect = GenerationError("network blip")

        # when / then
        assert service.judge_task_outcome("transcript", "cond") is None
        assert mock_broker.generate.call_count == 1

    def test_should_include_transcript_and_condition_in_prompt(self, service, mock_broker):
        # given
        mock_broker.generate.return_value = "SUCCESS"

        # when
        service.judge_task_outcome("[user] quiero un cafe y un pan", "orders a drink and food")

        # then
        (prompt,), _ = mock_broker.generate.call_args
        assert "[user] quiero un cafe y un pan" in prompt
        assert "orders a drink and food" in prompt
