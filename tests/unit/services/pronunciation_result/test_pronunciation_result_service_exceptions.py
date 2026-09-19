"""Exception dispatch: which raw failure maps to which wrapper tier, and that
every wrap is logged exactly once. No DependencyValidation tier -- the table
has no unique constraint, so IntegrityError is a plain storage failure."""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from api.models.foundations.pronunciation_result.exceptions import (
    FailedPronunciationResultStorageException,
    PronunciationResultDependencyException,
    PronunciationResultServiceException,
)


class TestDependencyTier:

    def test_should_wrap_operational_error_on_create(
        self, service, mock_pronunciation_result_broker, mock_logging_broker, make_result
    ):
        mock_pronunciation_result_broker.insert_pronunciation_result.side_effect = OperationalError(
            "INSERT", {}, Exception("connection refused")
        )

        with pytest.raises(PronunciationResultDependencyException) as caught:
            service.create_pronunciation_result(make_result())

        assert isinstance(caught.value.inner_exception, FailedPronunciationResultStorageException)
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 1
        assert mock_pronunciation_result_broker.select_all_pronunciation_results.call_count == 0
        assert mock_logging_broker.log_error.call_count == 1

    def test_should_wrap_operational_error_on_list(
        self, service, mock_pronunciation_result_broker, mock_logging_broker
    ):
        mock_pronunciation_result_broker.select_all_pronunciation_results.side_effect = OperationalError(
            "SELECT", {}, Exception("connection refused")
        )

        with pytest.raises(PronunciationResultDependencyException):
            service.list_pronunciation_results()

        assert mock_pronunciation_result_broker.select_all_pronunciation_results.call_count == 1
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 0
        assert mock_logging_broker.log_error.call_count == 1

    def test_should_wrap_integrity_error_as_plain_dependency(
        self, service, mock_pronunciation_result_broker, mock_logging_broker, make_result
    ):
        mock_pronunciation_result_broker.insert_pronunciation_result.side_effect = IntegrityError(
            "INSERT", {}, Exception("not-null violation")
        )

        with pytest.raises(PronunciationResultDependencyException) as caught:
            service.create_pronunciation_result(make_result())

        assert isinstance(caught.value.inner_exception, FailedPronunciationResultStorageException)
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 1
        assert mock_logging_broker.log_error.call_count == 1


class TestServiceTier:

    def test_should_wrap_unexpected_error_as_service_exception(
        self, service, mock_pronunciation_result_broker, mock_logging_broker
    ):
        mock_pronunciation_result_broker.select_all_pronunciation_results.side_effect = ValueError("boom")

        with pytest.raises(PronunciationResultServiceException) as caught:
            service.list_pronunciation_results()

        assert isinstance(caught.value.inner_exception, ValueError)
        assert mock_pronunciation_result_broker.select_all_pronunciation_results.call_count == 1
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 0
        assert mock_logging_broker.log_error.call_count == 1


class TestValidationTierLogging:

    def test_should_log_once_when_validation_fails(
        self, service, mock_pronunciation_result_broker, mock_logging_broker
    ):
        with pytest.raises(Exception):
            service.create_pronunciation_result(None)

        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 0
        assert mock_logging_broker.log_error.call_count == 1
