"""Unit tests for ConversationSessionService.start() -- double-start refusal.

BotProcessBroker.start() itself has no such guard by design (see its
docstring) -- this is the one piece of policy this service exists to add.

Pattern mirrors NL.Core.Entitlements.Api.Tests.Unit/Foundations/Entitlements/
EntitlementServiceTests.Validations.RetrieveById.cs:59-101
(ShouldThrowValidationExceptionOnRetrieveByIdIfEntitlementNotFoundAndLogItAsync).
"""

import pytest

from api.models.session_lifecycle.exceptions import (
    AlreadyRunningSessionException,
    SessionValidationException,
)


class TestConversationSessionServiceStartExceptions:

    def test_should_raise_session_already_running_exception_when_session_is_running(
        self, service, mock_broker, mock_logging_broker
    ):
        # given
        already_running_exception = AlreadyRunningSessionException()
        expected_validation_exception = SessionValidationException(
            inner_exception=already_running_exception
        )
        mock_broker.is_running.return_value = True

        # when
        with pytest.raises(SessionValidationException) as exc_info:
            service.start()

        # then
        actual = exc_info.value
        assert actual.args == expected_validation_exception.args
        assert type(actual.inner_exception) is type(expected_validation_exception.inner_exception)
        assert actual.inner_exception.args == expected_validation_exception.inner_exception.args

        mock_broker.is_running.assert_called_once_with()
        mock_broker.start.assert_not_called()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is SessionValidationException
        assert logged_exception.args == expected_validation_exception.args
        assert type(logged_exception.inner_exception) is type(expected_validation_exception.inner_exception)
