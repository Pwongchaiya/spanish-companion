"""Unit tests for PronunciationAssessmentService.assess_pronunciation() -- broker-failure and catch-all cases."""

import pytest

from api.models.foundations.pronunciation_assessment.exceptions import (
    PronunciationAssessmentDependencyException,
    PronunciationAssessmentServiceException,
    PronunciationAssessmentUnavailableError,
)
from tests.unit.services.pronunciation_assessment.conftest import VALID_TEXT, VALID_WAV


class TestPronunciationAssessmentServiceAssessExceptions:

    def test_should_wrap_broker_failure_in_dependency_exception(self, service, mock_broker, mock_logging_broker):
        # given
        mock_broker.assess.side_effect = RuntimeError("Azure Speech unreachable")

        # when
        with pytest.raises(PronunciationAssessmentDependencyException) as exc_info:
            service.assess_pronunciation(VALID_WAV, VALID_TEXT)

        # then
        assert isinstance(exc_info.value.inner_exception, PronunciationAssessmentUnavailableError)
        mock_broker.assess.assert_called_once_with(VALID_WAV, VALID_TEXT)
        mock_logging_broker.log_error.assert_called_once()
        logged = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged) is PronunciationAssessmentDependencyException

    def test_should_wrap_unexpected_exception_in_service_exception(self, service, mock_broker, mock_logging_broker):
        # given an unexpected non-broker failure inside the wrapped action
        boom = ValueError("unexpected")

        def action() -> None:
            raise boom

        # when
        with pytest.raises(PronunciationAssessmentServiceException) as exc_info:
            service._try_catch(action)

        # then
        assert exc_info.value.inner_exception is boom
        mock_broker.assess.assert_not_called()
        mock_logging_broker.log_error.assert_called_once()
        logged = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged) is PronunciationAssessmentServiceException
