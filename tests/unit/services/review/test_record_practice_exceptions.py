"""Unit tests for ReviewOrchestrator.record_practice() -- unknown flag_id.

An attempt against a flag that is not in the list is a client-side state
mismatch, not an orphan row worth writing -- so nothing must reach the
practice log.
"""

import pytest

from api.services.review import FlagNotFoundException


class TestReviewOrchestratorRecordPracticeExceptions:

    def test_should_raise_flag_not_found_without_recording_when_flag_id_is_unknown(
        self,
        service,
        mock_flag_broker,
        mock_practice_log_broker,
        make_flag,
    ):
        # given
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1")]

        # when / then
        with pytest.raises(FlagNotFoundException):
            service.record_practice("does-not-exist", "fui al mercado")

        mock_flag_broker.load_flags.assert_called_once_with()
        mock_practice_log_broker.record_attempt.assert_not_called()

    def test_should_raise_flag_not_found_when_flag_list_is_empty(
        self,
        service,
        mock_flag_broker,
        mock_practice_log_broker,
    ):
        # given
        mock_flag_broker.load_flags.return_value = []

        # when / then
        with pytest.raises(FlagNotFoundException):
            service.record_practice("flag-1", "fui al mercado")

        mock_flag_broker.load_flags.assert_called_once_with()
        mock_practice_log_broker.record_attempt.assert_not_called()
