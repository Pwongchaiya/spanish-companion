"""Unit tests for ConversationSessionService.stop() -- not-running refusal.

Fail-fast is the deliberate choice here (not a silent no-op) -- see
SessionNotRunningException's docstring in api/services/session_lifecycle.py
for the reasoning.
"""

import pytest

from api.services.session_lifecycle import SessionNotRunningException


class TestConversationSessionServiceStopExceptions:

    def test_should_raise_session_not_running_exception_when_no_session_is_running(
        self, service, mock_broker
    ):
        # given
        mock_broker.is_running.return_value = False

        # when / then
        with pytest.raises(SessionNotRunningException):
            service.stop()

        mock_broker.is_running.assert_called_once_with()
        mock_broker.send_graceful_signal.assert_not_called()
