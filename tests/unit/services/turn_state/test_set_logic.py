"""Unit tests for TurnStateService.set() -- pure delegation to the broker."""


class TestTurnStateServiceSet:

    def test_should_delegate_to_broker(self, service, mock_session_log_broker):
        # when
        service.set("thinking")

        # then
        mock_session_log_broker.write_turn_state.assert_called_once_with("thinking")
