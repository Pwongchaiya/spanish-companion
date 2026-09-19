"""Unit tests for ProgressOrchestrationService.list_pronunciation_trend."""

from datetime import datetime, timedelta

import pytest

from api.models.foundations.pronunciation_result.exceptions import (
    FailedPronunciationResultStorageException,
    PronunciationResultDependencyException,
)
from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult
from api.models.orchestrations.progress.exceptions import ProgressOrchestrationDependencyException
from api.models.orchestrations.progress.pronunciation_trend_point import PronunciationTrendPoint
from api.services.orchestrations.progress.progress_service import ProgressOrchestrationService
from tests.unit.services.progress.conftest import FIXED_NOW, FakeConfigurationBroker


def _result(i: int) -> PronunciationResult:
    return PronunciationResult(
        id=i,
        created_at=FIXED_NOW + timedelta(days=i),
        reference_text="perro",
        accuracy_score=float(i),
        fluency_score=float(i + 1),
        completeness_score=100.0,
        pronunciation_score=float(i + 2),
        prosody_score=None,
        words_json=[],
        locale="es-ES",
    )


class TestListPronunciationTrend:

    def test_should_return_empty_list_when_nothing_scored(self, service, mock_pronunciation_result_service):
        # given
        mock_pronunciation_result_service.list_pronunciation_results.return_value = []

        # when
        trend = service.list_pronunciation_trend()

        # then
        assert trend == []
        mock_pronunciation_result_service.list_pronunciation_results.assert_called_once_with()

    def test_should_map_fields_oldest_to_newest_with_overall_as_pronunciation_score(
        self, service, mock_pronunciation_result_service
    ):
        # given
        mock_pronunciation_result_service.list_pronunciation_results.return_value = [_result(1), _result(2)]

        # when
        trend = service.list_pronunciation_trend()

        # then
        assert trend == [
            PronunciationTrendPoint(created_at=FIXED_NOW + timedelta(days=1), accuracy=1.0, fluency=2.0, overall=3.0),
            PronunciationTrendPoint(created_at=FIXED_NOW + timedelta(days=2), accuracy=2.0, fluency=3.0, overall=4.0),
        ]

    def test_should_keep_only_last_n_where_n_comes_from_config(
        self, mock_learner_profile_processing_service, mock_mistake_pattern_service, mock_topic_covered_service,
        mock_session_log_entry_service, mock_pronunciation_result_service, mock_logging_broker
    ):
        # given
        svc = ProgressOrchestrationService(
            mock_learner_profile_processing_service,
            mock_mistake_pattern_service,
            mock_topic_covered_service,
            mock_session_log_entry_service,
            mock_pronunciation_result_service,
            logging_broker=mock_logging_broker,
            configuration_broker=FakeConfigurationBroker({"PRONUNCIATION_TREND_LIMIT": "2"}),
        )
        mock_pronunciation_result_service.list_pronunciation_results.return_value = [_result(i) for i in range(5)]

        # when
        trend = svc.list_pronunciation_trend()

        # then
        assert [p.accuracy for p in trend] == [3.0, 4.0]

    def test_should_default_limit_to_30(self, service, mock_pronunciation_result_service):
        # given
        mock_pronunciation_result_service.list_pronunciation_results.return_value = [_result(i) for i in range(40)]

        # when
        trend = service.list_pronunciation_trend()

        # then
        assert len(trend) == 30
        assert trend[-1].accuracy == 39.0

    def test_should_wrap_dependency_failure(self, service, mock_pronunciation_result_service, mock_logging_broker):
        # given
        wrapper = PronunciationResultDependencyException(inner_exception=FailedPronunciationResultStorageException("x"))
        mock_pronunciation_result_service.list_pronunciation_results.side_effect = wrapper

        # when
        with pytest.raises(ProgressOrchestrationDependencyException) as exc_info:
            service.list_pronunciation_trend()

        # then
        assert exc_info.value.inner_exception is wrapper
        mock_logging_broker.log_error.assert_called_once()

    @pytest.mark.parametrize("raw,expected", [("abc", 30), ("", 30), ("0", 0), ("-3", 0)])
    def test_should_fall_back_or_return_empty_for_bad_limit_config(
        self, raw, expected, mock_learner_profile_processing_service, mock_mistake_pattern_service,
        mock_topic_covered_service, mock_session_log_entry_service, mock_pronunciation_result_service,
        mock_logging_broker
    ):
        # given
        svc = ProgressOrchestrationService(
            mock_learner_profile_processing_service,
            mock_mistake_pattern_service,
            mock_topic_covered_service,
            mock_session_log_entry_service,
            mock_pronunciation_result_service,
            logging_broker=mock_logging_broker,
            configuration_broker=FakeConfigurationBroker({"PRONUNCIATION_TREND_LIMIT": raw}),
        )
        mock_pronunciation_result_service.list_pronunciation_results.return_value = [_result(i) for i in range(40)]

        # when
        trend = svc.list_pronunciation_trend()

        # then
        assert len(trend) == expected
        mock_pronunciation_result_service.list_pronunciation_results.assert_called_once_with()
