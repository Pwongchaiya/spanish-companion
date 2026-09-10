"""Unit tests for PracticeLogService.read_attempts() -- broker-failure path."""

import pytest

from api.models.foundations.practice_log.exceptions import (
    PracticeLogDependencyException,
    PracticeLogUnavailableError,
)


class TestPracticeLogServiceReadAttemptsExceptions:

    def test_should_raise_dependency_exception_when_broker_read_fails(
        self, service, mock_practice_log_broker, mock_logging_broker
    ):
        # given
        broker_error = OSError("disk read failed")
        mock_practice_log_broker.read_attempts.side_effect = broker_error

        # when
        with pytest.raises(PracticeLogDependencyException) as exc_info:
            service.read_attempts("flag-1")

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, PracticeLogUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_practice_log_broker.read_attempts.assert_called_once_with("flag-1")

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is PracticeLogDependencyException
        assert isinstance(logged_exception.inner_exception, PracticeLogUnavailableError)
