"""Unit tests for assess_and_record's validation tier: the assessment service's rejection is
wrapped, logged, and short-circuits before anything is persisted."""

import pytest

from api.models.foundations.pronunciation_assessment.exceptions import (
    InvalidPronunciationAssessmentRequestException,
    PronunciationAssessmentValidationException,
)
from api.models.orchestrations.pronunciation.exceptions import PronunciationOrchestrationValidationException
from tests.unit.services.pronunciation.conftest import TEXT, WAV


class TestAssessAndRecordValidation:

    def test_should_wrap_assessment_validation_exception_and_not_persist(
        self, service, mock_assessment_service, mock_result_service, mock_logging_broker
    ):
        # given
        wrapper = PronunciationAssessmentValidationException(
            inner_exception=InvalidPronunciationAssessmentRequestException()
        )
        mock_assessment_service.assess_pronunciation.side_effect = wrapper

        # when
        with pytest.raises(PronunciationOrchestrationValidationException) as exc_info:
            service.assess_and_record(WAV, TEXT)

        # then
        assert exc_info.value.inner_exception is wrapper
        leaf = exc_info.value.inner_exception.inner_exception
        assert isinstance(leaf, InvalidPronunciationAssessmentRequestException)
        mock_assessment_service.assess_pronunciation.assert_called_once_with(WAV, TEXT)
        mock_result_service.create_pronunciation_result.assert_not_called()
        mock_logging_broker.log_error.assert_called_once()
