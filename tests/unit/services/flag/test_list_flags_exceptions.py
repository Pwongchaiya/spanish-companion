"""Unit tests for FlagService.list_flags() -- broker-failure path.

H7 of the architecture conformance audit: this method was a bare pass-through,
so anything FlagBroker.load_flags() raised escaped the service unwrapped and
reached Flask raw. The "missing or corrupt file -> []" tolerance the broker
guarantees is a separate case and still returns [] rather than raising -- that
is covered in test_list_flags_logic.py.

Mirrors test_get_flag_exceptions.py's dependency case, the same broker method
failing the same way.
"""

import pytest

from api.models.flag.exceptions import FlagDependencyException, FlagUnavailableError


class TestFlagServiceListFlagsExceptions:

    def test_should_raise_dependency_exception_when_broker_load_fails(
        self, service, mock_flag_broker, mock_logging_broker
    ):
        # given -- e.g. a permission error or disk failure reading the flag file
        broker_error = OSError("disk read failed")
        mock_flag_broker.load_flags.side_effect = broker_error

        # when
        with pytest.raises(FlagDependencyException) as exc_info:
            service.list_flags()

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, FlagUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_flag_broker.load_flags.assert_called_once_with()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is FlagDependencyException
