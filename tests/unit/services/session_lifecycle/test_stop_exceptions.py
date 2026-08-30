"""Unit tests for ConversationSessionService.stop() -- not-running refusal.

Fail-fast is the deliberate choice here (not a silent no-op) -- see
NotRunningSessionException's docstring in api/services/session_lifecycle.py
for the reasoning.

Pattern mirrors NL.Core.Entitlements.Api.Tests.Unit/Foundations/Entitlements/
EntitlementServiceTests.Validations.RetrieveById.cs:59-101
(ShouldThrowValidationExceptionOnRetrieveByIdIfEntitlementNotFoundAndLogItAsync).
"""

import pytest

from api.models.session_lifecycle.exceptions import (
    NotRunningSessionException,
    SessionValidationException,
)


class TestConversationSessionServiceStopExceptions:

    def test_should_raise_session_not_running_exception_when_no_session_is_running(
        self, service, mock_broker, mock_logging_broker
    ):
        # given
        not_running_exception = NotRunningSessionException()
        expected_validation_exception = SessionValidationException(
            inner_exception=not_running_exception
        )
        mock_broker.is_running.return_value = False

        # when
        with pytest.raises(SessionValidationException) as exc_info:
            service.stop()

        # then
        actual = exc_info.value
        assert actual.args == expected_validation_exception.args
        assert type(actual.inner_exception) is type(expected_validation_exception.inner_exception)
        assert actual.inner_exception.args == expected_validation_exception.inner_exception.args

        mock_broker.is_running.assert_called_once_with()
        mock_broker.send_graceful_signal.assert_not_called()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is SessionValidationException
        assert logged_exception.args == expected_validation_exception.args
        assert type(logged_exception.inner_exception) is type(expected_validation_exception.inner_exception)
