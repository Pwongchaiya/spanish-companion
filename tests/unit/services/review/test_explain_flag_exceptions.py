"""Unit tests for ReviewOrchestrator.explain_flag() -- unknown flag_id.

The lookup happens before any retrieval or generation work, so an unknown id
must cost nothing downstream.
"""

import pytest

from api.services.review import FlagNotFoundException


class TestReviewOrchestratorExplainFlagExceptions:

    def test_should_raise_flag_not_found_before_retrieval_when_flag_id_is_unknown(
        self,
        service,
        mock_flag_broker,
        mock_retrieval_controller,
        mock_generation_controller,
        make_flag,
    ):
        # given
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1")]

        # when / then
        with pytest.raises(FlagNotFoundException):
            service.explain_flag("does-not-exist")

        mock_flag_broker.load_flags.assert_called_once_with()
        mock_retrieval_controller.retrieve.assert_not_called()
        mock_generation_controller.explain.assert_not_called()

    def test_should_raise_flag_not_found_when_flag_list_is_empty(
        self,
        service,
        mock_flag_broker,
        mock_retrieval_controller,
        mock_generation_controller,
    ):
        # given
        mock_flag_broker.load_flags.return_value = []

        # when / then
        with pytest.raises(FlagNotFoundException):
            service.explain_flag("flag-1")

        mock_flag_broker.load_flags.assert_called_once_with()
        mock_retrieval_controller.retrieve.assert_not_called()
        mock_generation_controller.explain.assert_not_called()
