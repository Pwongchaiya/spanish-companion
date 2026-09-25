"""Unit tests for FlagService.save_session_flags() -- validation and
broker-failure paths. Same contract as save_flags(), see
test_save_flags_exceptions.py."""

import pytest

from api.models.foundations.flag.exceptions import (
    FlagDependencyException,
    FlagUnavailableError,
    FlagValidationException,
    InvalidFlagStatusException,
)


class TestFlagServiceSaveSessionFlagsExceptions:

    def test_should_raise_validation_exception_when_status_is_not_a_known_value(
        self, service, mock_flag_broker, mock_logging_broker, make_flag
    ):
        # given
        flag = make_flag("flag-1")
        flag.status = "archived"

        # when
        with pytest.raises(FlagValidationException) as exc_info:
            service.save_session_flags(4, [flag])

        # then
        assert isinstance(exc_info.value.inner_exception, InvalidFlagStatusException)
        mock_flag_broker.save_session_flags.assert_not_called()

    def test_should_raise_dependency_exception_when_broker_save_fails(
        self, service, mock_flag_broker, mock_logging_broker, make_flag
    ):
        # given
        flags = [make_flag("flag-1")]
        broker_error = OSError("disk write failed")
        mock_flag_broker.save_session_flags.side_effect = broker_error

        # when
        with pytest.raises(FlagDependencyException) as exc_info:
            service.save_session_flags(4, flags)

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, FlagUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_flag_broker.save_session_flags.assert_called_once_with(4, flags)
        mock_logging_broker.log_error.assert_called_once()
