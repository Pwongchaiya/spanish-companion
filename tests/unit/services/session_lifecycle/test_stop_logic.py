"""Unit tests for ConversationSessionService.stop() -- the graceful ->
terminate -> kill escalation policy and `graceful` outcome tracking.

See test_stop_exceptions.py for the not-running refusal.
"""

import subprocess

import pytest
from unittest.mock import call

from api.services.foundations.session_lifecycle import (
    GRACEFUL_TIMEOUT_SECONDS,
    TERMINATE_TIMEOUT_SECONDS,
)


def _timeout(seconds: float) -> subprocess.TimeoutExpired:
    return subprocess.TimeoutExpired(cmd="bot", timeout=seconds)


class TestConversationSessionServiceStop:

    def test_should_stop_gracefully_when_graceful_signal_is_honoured(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = True
        mock_broker.wait.return_value = None

        # when
        service.stop()

        # then
        mock_broker.is_running.assert_called_once_with()
        mock_broker.send_graceful_signal.assert_called_once_with()
        mock_broker.wait.assert_called_once_with(GRACEFUL_TIMEOUT_SECONDS)
        mock_broker.terminate.assert_not_called()
        mock_broker.kill.assert_not_called()

    def test_should_record_graceful_true_when_graceful_signal_is_honoured(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = True
        mock_broker.wait.return_value = None

        # when
        service.stop()
        status = service.get_status()

        # then
        assert status.graceful is True

    def test_should_terminate_when_graceful_signal_times_out(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = True
        mock_broker.wait.side_effect = [_timeout(GRACEFUL_TIMEOUT_SECONDS), None]

        # when
        service.stop()

        # then
        mock_broker.is_running.assert_called_once_with()
        mock_broker.terminate.assert_called_once_with()
        mock_broker.kill.assert_not_called()
        assert mock_broker.wait.call_args_list == [
            call(GRACEFUL_TIMEOUT_SECONDS),
            call(TERMINATE_TIMEOUT_SECONDS),
        ]

    def test_should_record_graceful_false_when_terminate_is_needed(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = True
        mock_broker.wait.side_effect = [_timeout(GRACEFUL_TIMEOUT_SECONDS), None]

        # when
        service.stop()
        status = service.get_status()

        # then
        assert status.graceful is False

    def test_should_kill_when_terminate_also_times_out(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = True
        mock_broker.wait.side_effect = [
            _timeout(GRACEFUL_TIMEOUT_SECONDS),
            _timeout(TERMINATE_TIMEOUT_SECONDS),
            None,
        ]

        # when
        service.stop()

        # then
        mock_broker.is_running.assert_called_once_with()
        mock_broker.terminate.assert_called_once_with()
        mock_broker.kill.assert_called_once_with()
        assert mock_broker.wait.call_args_list == [
            call(GRACEFUL_TIMEOUT_SECONDS),
            call(TERMINATE_TIMEOUT_SECONDS),
            call(TERMINATE_TIMEOUT_SECONDS),
        ]

    def test_should_record_graceful_false_when_kill_is_needed(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = True
        mock_broker.wait.side_effect = [
            _timeout(GRACEFUL_TIMEOUT_SECONDS),
            _timeout(TERMINATE_TIMEOUT_SECONDS),
            None,
        ]

        # when
        service.stop()
        status = service.get_status()

        # then
        assert status.graceful is False

    def test_should_propagate_timeout_expired_when_kill_is_not_honoured(self, service, mock_broker):
        # given -- OS-level anomaly: SIGKILL/TerminateProcess sent but the
        # process was never reaped. Outside this feature's two-exception
        # vocabulary by design (see session_lifecycle.py's stop() comment).
        mock_broker.is_running.return_value = True
        mock_broker.wait.side_effect = [
            _timeout(GRACEFUL_TIMEOUT_SECONDS),
            _timeout(TERMINATE_TIMEOUT_SECONDS),
            _timeout(TERMINATE_TIMEOUT_SECONDS),
        ]

        # when / then
        with pytest.raises(subprocess.TimeoutExpired):
            service.stop()

        mock_broker.is_running.assert_called_once_with()
        mock_broker.kill.assert_called_once_with()
        assert mock_broker.wait.call_args_list == [
            call(GRACEFUL_TIMEOUT_SECONDS),
            call(TERMINATE_TIMEOUT_SECONDS),
            call(TERMINATE_TIMEOUT_SECONDS),
        ]
