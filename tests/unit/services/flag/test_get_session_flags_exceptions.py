"""Unit tests for FlagService.get_session_flags() -- broker-failure path."""

import pytest

from api.models.foundations.flag.exceptions import FlagDependencyException, FlagUnavailableError


class TestFlagServiceGetSessionFlagsExceptions:

    def test_should_raise_dependency_exception_when_broker_read_fails(
        self, service, mock_flag_broker, mock_logging_broker
    ):
        # given
        broker_error = OSError("disk read failed")
        mock_flag_broker.get_session_flags.side_effect = broker_error

        # when
        with pytest.raises(FlagDependencyException) as exc_info:
            service.get_session_flags(4)

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, FlagUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_flag_broker.get_session_flags.assert_called_once_with(4)
        mock_logging_broker.log_error.assert_called_once()
