"""Unit tests for assess_and_record's dependency and service tiers."""

import pytest

from api.models.foundations.pronunciation_assessment.exceptions import (
    PronunciationAssessmentDependencyException,
    PronunciationAssessmentUnavailableError,
)
from api.models.foundations.pronunciation_result.exceptions import (
    FailedPronunciationResultStorageException,
    InvalidPronunciationResultException,
    PronunciationResultDependencyException,
    PronunciationResultValidationException,
)
from api.models.orchestrations.pronunciation.exceptions import (
    FailedPronunciationOrchestrationServiceException,
    PronunciationOrchestrationDependencyException,
    PronunciationOrchestrationServiceException,
)
from tests.unit.services.pronunciation.conftest import TEXT, WAV


class TestAssessAndRecordExceptions:

    def test_should_wrap_assessment_dependency_exception_and_not_persist(
        self, service, mock_assessment_service, mock_result_service, mock_logging_broker
    ):
        # given
        wrapper = PronunciationAssessmentDependencyException(
            inner_exception=PronunciationAssessmentUnavailableError("azure down")
        )
        mock_assessment_service.assess_pronunciation.side_effect = wrapper

        # when
        with pytest.raises(PronunciationOrchestrationDependencyException) as exc_info:
            service.assess_and_record(WAV, TEXT)

        # then
        assert exc_info.value.inner_exception is wrapper
        mock_assessment_service.assess_pronunciation.assert_called_once_with(WAV, TEXT)
        mock_result_service.create_pronunciation_result.assert_not_called()
        mock_logging_broker.log_error.assert_called_once()

    def test_should_surface_persist_failure_after_successful_assessment_as_dependency_exception(
        self, service, mock_assessment_service, mock_result_service, assessment, mock_logging_broker
    ):
        # given
        mock_assessment_service.assess_pronunciation.return_value = assessment
        wrapper = PronunciationResultDependencyException(
            inner_exception=FailedPronunciationResultStorageException("db down")
        )
        mock_result_service.create_pronunciation_result.side_effect = wrapper

        # when
        with pytest.raises(PronunciationOrchestrationDependencyException) as exc_info:
            service.assess_and_record(WAV, TEXT)

        # then
        assert exc_info.value.inner_exception is wrapper
        mock_assessment_service.assess_pronunciation.assert_called_once_with(WAV, TEXT)
        mock_result_service.create_pronunciation_result.assert_called_once()
        mock_logging_broker.log_error.assert_called_once()

    def test_should_wrap_result_validation_exception_as_service_exception_not_400_tier(
        self, service, mock_assessment_service, mock_result_service, assessment, mock_logging_broker
    ):
        # given
        mock_assessment_service.assess_pronunciation.return_value = assessment
        leaf = PronunciationResultValidationException(inner_exception=InvalidPronunciationResultException())
        mock_result_service.create_pronunciation_result.side_effect = leaf

        # when
        with pytest.raises(PronunciationOrchestrationServiceException) as exc_info:
            service.assess_and_record(WAV, TEXT)

        # then
        assert isinstance(exc_info.value.inner_exception, FailedPronunciationOrchestrationServiceException)
        assert exc_info.value.inner_exception.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_wrap_unexpected_exception_in_service_exception(
        self, service, mock_assessment_service, mock_result_service, mock_logging_broker
    ):
        # given
        boom = RuntimeError("boom")
        mock_assessment_service.assess_pronunciation.side_effect = boom

        # when
        with pytest.raises(PronunciationOrchestrationServiceException) as exc_info:
            service.assess_and_record(WAV, TEXT)

        # then
        assert isinstance(exc_info.value.inner_exception, FailedPronunciationOrchestrationServiceException)
        assert exc_info.value.inner_exception.inner_exception is boom
        mock_result_service.create_pronunciation_result.assert_not_called()
        mock_logging_broker.log_error.assert_called_once()
