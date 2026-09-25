"""Unit tests for SessionRecapAggregationService's exception wrapping, per
session_recap_aggregation_service_exceptions.py's three-tier _try_catch.
"""

import pytest

from api.models.aggregations.session_recap.exceptions import (
    SessionRecapAggregationDependencyException,
    SessionRecapAggregationServiceException,
    SessionRecapAggregationValidationException,
)
from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
    ProgressOrchestrationValidationException,
)
from api.models.orchestrations.review.exceptions import ReviewOrchestrationServiceException


class TestSessionRecapAggregationServiceExceptions:

    def test_should_raise_aggregation_validation_exception_when_progress_service_raises_validation(
        self, service, mock_progress_service, mock_logging_broker
    ):
        leaf = ProgressOrchestrationValidationException(inner_exception=ValueError("bad input"))
        mock_progress_service.get_latest_completed_session.side_effect = leaf

        with pytest.raises(SessionRecapAggregationValidationException) as exc_info:
            service.get_latest_recap()

        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_aggregation_dependency_exception_when_progress_service_raises_dependency(
        self, service, mock_progress_service, mock_logging_broker
    ):
        leaf = ProgressOrchestrationDependencyException(inner_exception=RuntimeError("storage down"))
        mock_progress_service.get_latest_completed_session.side_effect = leaf

        with pytest.raises(SessionRecapAggregationDependencyException) as exc_info:
            service.get_latest_recap()

        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_aggregation_service_exception_when_progress_services_own_service_exception_is_not_caught_by_name(  # noqa: E501
        self, service, mock_progress_service, mock_logging_broker
    ):
        # ProgressOrchestrationServiceException is deliberately absent from
        # the validation/dependency except clauses, so it must fall through
        # to the catch-all tier, not go unwrapped.
        mock_progress_service.get_latest_completed_session.side_effect = ProgressOrchestrationServiceException(
            inner_exception=RuntimeError("unexpected")
        )

        with pytest.raises(SessionRecapAggregationServiceException):
            service.get_latest_recap()

        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_aggregation_service_exception_when_review_service_raises(
        self, service, mock_progress_service, mock_review_service, mock_logging_broker, make_session_log_entry
    ):
        # list_flags() only ever raises ReviewOrchestrationServiceException
        # (no Validation/Dependency tier for this method) -- it has no named
        # catch here either, so it always falls to the catch-all.
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry()
        mock_review_service.list_flags.side_effect = ReviewOrchestrationServiceException(
            inner_exception=RuntimeError("flags.json unreadable")
        )

        with pytest.raises(SessionRecapAggregationServiceException):
            service.get_latest_recap()

        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_aggregation_service_exception_when_an_unexpected_error_occurs(
        self, service, mock_progress_service, mock_logging_broker
    ):
        mock_progress_service.get_latest_completed_session.side_effect = ValueError("boom")

        with pytest.raises(SessionRecapAggregationServiceException):
            service.get_latest_recap()

        mock_logging_broker.log_error.assert_called_once()


class TestGetLatestRecapSpeechExceptions:

    def test_should_keep_dependency_tier_when_progress_raises_dependency(
        self, service, mock_progress_service, mock_tts_service
    ):
        mock_progress_service.get_latest_completed_session.side_effect = ProgressOrchestrationDependencyException(
            inner_exception=Exception("db down")
        )

        with pytest.raises(SessionRecapAggregationDependencyException):
            service.get_latest_recap_speech()

        mock_progress_service.get_latest_completed_session.assert_called_once_with()
        mock_tts_service.synthesize_speech.assert_not_called()

    def test_should_wrap_tts_failure_as_service_exception(
        self, service, mock_progress_service, mock_review_service, mock_tts_service, make_session_log_entry
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=0)
        mock_review_service.list_flags.return_value = []
        mock_tts_service.synthesize_speech.side_effect = Exception("azure down")

        with pytest.raises(SessionRecapAggregationServiceException):
            service.get_latest_recap_speech()

        mock_tts_service.synthesize_speech.assert_called_once()
