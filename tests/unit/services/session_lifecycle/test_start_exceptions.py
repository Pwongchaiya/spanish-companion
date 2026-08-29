"""Unit tests for ConversationSessionService.start() -- double-start refusal.

BotProcessBroker.start() itself has no such guard by design (see its
docstring) -- this is the one piece of policy this service exists to add.
"""

import pytest

from api.services.session_lifecycle import SessionAlreadyRunningException


class TestConversationSessionServiceStartExceptions:

    def test_should_raise_session_already_running_exception_when_session_is_running(
        self, service, mock_broker
    ):
        # given
        mock_broker.is_running.return_value = True

        # when / then
        with pytest.raises(SessionAlreadyRunningException):
            service.start()

        mock_broker.is_running.assert_called_once_with()
        mock_broker.start.assert_not_called()
