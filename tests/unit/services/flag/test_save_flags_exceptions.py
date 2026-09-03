"""Unit tests for FlagService.save_flags() -- broker-failure path."""

import pytest

from api.models.flag.exceptions import FlagDependencyException, FlagUnavailableError


class TestFlagServiceSaveFlagsExceptions:

    def test_should_raise_dependency_exception_when_broker_save_fails(
        self, service, mock_flag_broker, mock_logging_broker, make_flag
    ):
        # given
        flags = [make_flag("flag-1")]
        broker_error = OSError("disk write failed")
        mock_flag_broker.save_flags.side_effect = broker_error

        # when
        with pytest.raises(FlagDependencyException) as exc_info:
            service.save_flags(flags)

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, FlagUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_flag_broker.save_flags.assert_called_once_with(flags)

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is FlagDependencyException
        assert isinstance(logged_exception.inner_exception, FlagUnavailableError)
