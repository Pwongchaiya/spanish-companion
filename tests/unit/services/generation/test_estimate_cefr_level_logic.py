"""Unit tests for GenerationService.estimate_cefr_level() -- roadmap A6.

Same shape as judge_practice_attempt(): one broker call, swallow failure/
unparseable output to a safe sentinel (None here, False there) rather than
raising, so a bad LLM response never corrupts learner_profile.cefr_estimate.
"""

from rag.brokers.generation import GenerationError


class TestGenerationServiceEstimateCefrLevel:

    def test_should_return_parsed_level_when_broker_answers_a_valid_code(self, service, mock_broker):
        # given
        mock_broker.generate.return_value = "B1, solid intermediate vocabulary."

        # when
        result = service.estimate_cefr_level("[user] hola\n[assistant] hola, como estas")

        # then
        assert result == "B1"

    def test_should_uppercase_a_lowercase_level(self, service, mock_broker):
        # given
        mock_broker.generate.return_value = "b2"

        # when
        result = service.estimate_cefr_level("some transcript")

        # then
        assert result == "B2"

    def test_should_return_none_when_broker_answer_is_unparseable(self, service, mock_broker):
        # given
        mock_broker.generate.return_value = "I'm not sure, hard to tell."

        # when
        result = service.estimate_cefr_level("some transcript")

        # then
        assert result is None

    def test_should_return_none_when_broker_call_fails(self, service, mock_broker):
        # given
        mock_broker.generate.side_effect = GenerationError("network blip")

        # when
        result = service.estimate_cefr_level("some transcript")

        # then -- can't estimate, so skip rather than guess
        assert result is None

    def test_should_include_transcript_text_in_prompt(self, service, mock_broker):
        # given
        mock_broker.generate.return_value = "A2"

        # when
        service.estimate_cefr_level("[user] quiero comer tacos")

        # then
        (prompt,), _ = mock_broker.generate.call_args
        assert "[user] quiero comer tacos" in prompt
