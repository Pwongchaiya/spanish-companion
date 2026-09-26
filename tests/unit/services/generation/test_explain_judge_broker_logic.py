"""Unit tests for GenerationService.explain()'s #68 `judge_broker` split.

_is_grounded's reflective judge call used to share `broker` with the draft
call -- both at whatever (usually nonzero) temperature the caller's broker
was built with, so the judge could randomly reject a good draft. A caller
may now pass a dedicated `judge_broker` (e.g. one pinned to temperature 0);
when it's not given, behaviour is unchanged -- the judge call still goes to
`broker`, same as today.
"""

from unittest.mock import Mock

from rag.brokers.generation import GenerationBroker
from rag.services.foundations.generation import GenerationService


class TestGenerationServiceJudgeBroker:

    def test_should_send_draft_to_broker_once_and_judge_prompt_to_judge_broker_once_when_judge_broker_given(
        self, mock_broker, mock_logging_broker, configuration_broker, flag, chunks
    ):
        # given
        judge_broker = Mock(spec=GenerationBroker)
        mock_broker.generate.side_effect = ["some explanation"]
        judge_broker.generate.side_effect = ["YES, grounded"]
        service = GenerationService(
            broker=mock_broker,
            logging_broker=mock_logging_broker,
            configuration_broker=configuration_broker,
            judge_broker=judge_broker,
        )

        # when
        service.explain(flag, chunks)

        # then -- draft goes to broker exactly once, judge prompt to judge_broker
        # exactly once; broker never sees the judge prompt.
        assert mock_broker.generate.call_count == 1
        assert judge_broker.generate.call_count == 1
        (judge_prompt,), _ = judge_broker.generate.call_args_list[0]
        assert "some explanation" in judge_prompt

    def test_should_send_both_draft_and_judge_prompt_to_broker_when_no_judge_broker_given(
        self, mock_broker, mock_logging_broker, configuration_broker, flag, chunks
    ):
        # given -- no judge_broker passed, same construction as every other
        # existing test/caller.
        mock_broker.generate.side_effect = ["some explanation", "YES, grounded"]
        service = GenerationService(
            broker=mock_broker,
            logging_broker=mock_logging_broker,
            configuration_broker=configuration_broker,
        )

        # when
        service.explain(flag, chunks)

        # then -- both calls go to the single broker (draft, then judge).
        assert mock_broker.generate.call_count == 2
