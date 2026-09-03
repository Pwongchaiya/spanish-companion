"""Unit tests for FlagService.get_flag() -- not-found and broker-failure paths.

Pattern mirrors NL.Core.Entitlements.Api.Tests.Unit/Foundations/Entitlements/
EntitlementServiceTests.Validations.RetrieveById.cs:59-101
(ShouldThrowValidationExceptionOnRetrieveByIdIfEntitlementNotFoundAndLogItAsync).
"""

import pytest

from api.models.flag.exceptions import (
    FlagDependencyException,
    FlagUnavailableError,
    FlagValidationException,
    NotFoundFlagException,
)


class TestFlagServiceGetFlagExceptions:

    def test_should_raise_validation_exception_when_flag_id_does_not_exist(
        self, service, mock_flag_broker, mock_logging_broker, make_flag
    ):
        # given
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1")]
        expected_leaf = NotFoundFlagException("does-not-exist")

        # when
        with pytest.raises(FlagValidationException) as exc_info:
            service.get_flag("does-not-exist")

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, NotFoundFlagException)
        assert actual.inner_exception.args == expected_leaf.args

        mock_flag_broker.load_flags.assert_called_once_with()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is FlagValidationException
        assert isinstance(logged_exception.inner_exception, NotFoundFlagException)

    def test_should_raise_dependency_exception_when_broker_load_fails(
        self, service, mock_flag_broker, mock_logging_broker
    ):
        # given -- e.g. a permission error or disk failure reading the flag
        # file; distinct from the "file missing/corrupt -> []" tolerance
        # FlagBroker.load_flags() otherwise guarantees.
        broker_error = OSError("disk read failed")
        mock_flag_broker.load_flags.side_effect = broker_error

        # when
        with pytest.raises(FlagDependencyException) as exc_info:
            service.get_flag("flag-1")

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, FlagUnavailableError)
        assert actual.inner_exception.args == (str(broker_error),)

        mock_flag_broker.load_flags.assert_called_once_with()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is FlagDependencyException
        assert isinstance(logged_exception.inner_exception, FlagUnavailableError)
