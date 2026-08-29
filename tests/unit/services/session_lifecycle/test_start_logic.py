"""Unit tests for ConversationSessionService.start() -- happy path.

See test_start_exceptions.py for the double-start refusal.
"""


class TestConversationSessionServiceStart:

    def test_should_start_broker_when_no_session_is_running(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = False

        # when
        service.start()

        # then
        mock_broker.is_running.assert_called_once_with()
        mock_broker.start.assert_called_once_with()
