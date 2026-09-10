"""Unit tests for PracticeLogService.record_attempt() -- attempt_text
validation.

Verbatim port of ReviewOrchestratorValidations._validate_practice_input; see
practice_log_service_validations.py.
"""

import pytest

from api.models.foundations.practice_log.exceptions import (
    InvalidPracticeAttemptException,
    PracticeLogValidationException,
)


class TestPracticeLogServiceRecordAttemptValidation:

    @pytest.mark.parametrize("blank_text", ["", "   ", "\n\t"])
    def test_should_raise_validation_exception_when_attempt_text_is_blank(
        self, service, mock_practice_log_broker, mock_logging_broker, make_attempt, blank_text
    ):
        # given
        attempt = make_attempt(attempt_text=blank_text)
        expected_leaf = InvalidPracticeAttemptException()

        # when
        with pytest.raises(PracticeLogValidationException) as exc_info:
            service.record_attempt(attempt)

        # then
        actual = exc_info.value
        assert isinstance(actual.inner_exception, InvalidPracticeAttemptException)
        assert actual.inner_exception.args == expected_leaf.args

        mock_practice_log_broker.record_attempt.assert_not_called()

        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is PracticeLogValidationException
        assert isinstance(logged_exception.inner_exception, InvalidPracticeAttemptException)

    def test_should_raise_validation_exception_when_attempt_text_is_not_a_string(
        self, service, mock_practice_log_broker, mock_logging_broker, make_attempt
    ):
        # given -- a caller bypassing type hints at runtime (e.g. a bad
        # deserialization) hits the isinstance() branch, not just .strip().
        attempt = make_attempt(attempt_text=None)

        # when
        with pytest.raises(PracticeLogValidationException) as exc_info:
            service.record_attempt(attempt)

        # then
        assert isinstance(exc_info.value.inner_exception, InvalidPracticeAttemptException)
        mock_practice_log_broker.record_attempt.assert_not_called()
