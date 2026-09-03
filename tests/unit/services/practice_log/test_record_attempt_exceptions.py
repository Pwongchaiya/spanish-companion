"""Unit tests for PracticeLogService.record_attempt() -- broker-failure path."""

import pytest

from api.models.practice_log.exceptions import (
    PracticeLogDependencyException,
    PracticeLogUnavailableError,
)


class TestPracticeLogServiceRecordAttemptExceptions:

    def test_should_raise_dependency_exception_when_broker_record_fails(
        self, service, mock_practice_log_broker, mock_logging_broker, make_attempt
    ):
        # given
        attempt = make_attempt()
        broker_error = OSError("disk append failed")
        mock_practice_log_broker.record_attempt.side_effect = broker_error

        # when
        with pytest.raises(PracticeLogDependencyException) as exc_info:
            service.record_attempt(attempt)

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, PracticeLogUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_practice_log_broker.record_attempt.assert_called_once_with(attempt)

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is PracticeLogDependencyException
        assert isinstance(logged_exception.inner_exception, PracticeLogUnavailableError)
