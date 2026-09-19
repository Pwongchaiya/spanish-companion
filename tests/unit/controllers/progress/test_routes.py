"""Unit tests for the Progress blueprint's HTTP mapping.

Per CLAUDE.md's Phase 2 test strategy: this tier verifies HTTP mapping only
(status codes, JSON shape, isoformat timestamps) -- never Progress's actual
read logic. ProgressOrchestrationService is mocked via
unittest.mock.Mock(spec=ProgressOrchestrationService);
tests/unit/services/progress/ covers the real logic.

All four routes take no input, so there is no validation-shaped 400
case -- same two-tier exception mapping (Dependency/Service only) as
Review's GET /review/flags.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from flask import Flask

from api.exposers.progress import make_progress_blueprint
from api.models.aggregations.session_recap.exceptions import (
    SessionRecapAggregationDependencyException,
    SessionRecapAggregationServiceException,
)
from api.models.aggregations.session_recap.session_recap import SessionRecap
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
)
from api.models.orchestrations.progress.speaking_total import SpeakingTotal
from api.models.orchestrations.progress.topic_coverage_entry import TopicCoverageEntry
from api.models.orchestrations.progress.unflagged_streak import UnflaggedStreak
from api.services.aggregations.session_recap import SessionRecapAggregationService
from api.services.orchestrations.progress import ProgressOrchestrationService


@pytest.fixture
def mock_orchestrator():
    return Mock(spec=ProgressOrchestrationService)


@pytest.fixture
def mock_recap_aggregator():
    return Mock(spec=SessionRecapAggregationService)


@pytest.fixture
def client(mock_orchestrator, mock_recap_aggregator):
    app = Flask(__name__)
    app.register_blueprint(make_progress_blueprint(mock_orchestrator, mock_recap_aggregator))
    return app.test_client()


class TestListMistakes:

    def test_should_return_200_with_isoformat_timestamp_when_patterns_exist(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_mistake_summary.return_value = [
            MistakePattern(
                id=1,
                profile_id=1,
                category="ser_estar",
                occurrence_count=3,
                last_seen_at=datetime(2026, 9, 1, 12, 0, 0),
                status="active",
            )
        ]

        # when
        response = client.get("/progress/mistakes")

        # then
        assert response.status_code == 200
        assert response.get_json() == [
            {
                "id": 1,
                "profile_id": 1,
                "category": "ser_estar",
                "occurrence_count": 3,
                "last_seen_at": "2026-09-01T12:00:00",
                "status": "active",
            }
        ]
        mock_orchestrator.list_mistake_summary.assert_called_once_with()

    def test_should_omit_scheduler_fields_when_pattern_is_scheduled(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_mistake_summary.return_value = [
            MistakePattern(
                id=1,
                profile_id=1,
                category="ser_estar",
                occurrence_count=3,
                last_seen_at=datetime(2026, 9, 1, 12, 0, 0),
                status="active",
                interval_days=4.0,
                next_due_at=datetime(2026, 9, 5, 12, 0, 0),
            )
        ]

        # when
        response = client.get("/progress/mistakes")

        # then
        assert response.status_code == 200
        (body,) = response.get_json()
        assert "interval_days" not in body
        assert "next_due_at" not in body
        mock_orchestrator.list_mistake_summary.assert_called_once_with()

    def test_should_return_200_with_empty_list_when_no_patterns(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_mistake_summary.return_value = []

        # when
        response = client.get("/progress/mistakes")

        # then
        assert response.status_code == 200
        assert response.get_json() == []

    def test_should_return_500_when_orchestrator_raises_dependency_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_mistake_summary.side_effect = ProgressOrchestrationDependencyException(
            inner_exception=RuntimeError("db down")
        )

        # when
        response = client.get("/progress/mistakes")

        # then
        assert response.status_code == 500

    def test_should_return_500_when_orchestrator_raises_service_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_mistake_summary.side_effect = ProgressOrchestrationServiceException(
            inner_exception=RuntimeError("unexpected")
        )

        # when
        response = client.get("/progress/mistakes")

        # then
        assert response.status_code == 500


class TestListTopics:

    def test_should_return_200_with_covered_and_uncovered_entries(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_topic_coverage.return_value = [
            TopicCoverageEntry(topic="ser-vs-estar", covered=True, first_covered_at=datetime(2026, 1, 1)),
            TopicCoverageEntry(topic="subjunctive-basics", covered=False, first_covered_at=None),
        ]

        # when
        response = client.get("/progress/topics")

        # then
        assert response.status_code == 200
        assert response.get_json() == [
            {"topic": "ser-vs-estar", "covered": True, "first_covered_at": "2026-01-01T00:00:00"},
            {"topic": "subjunctive-basics", "covered": False, "first_covered_at": None},
        ]
        mock_orchestrator.list_topic_coverage.assert_called_once_with()

    def test_should_return_500_when_orchestrator_raises_dependency_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_topic_coverage.side_effect = ProgressOrchestrationDependencyException(
            inner_exception=RuntimeError("db down")
        )

        # when
        response = client.get("/progress/topics")

        # then
        assert response.status_code == 500


class TestGetSpeaking:
    """Roadmap C1. SpeakingTotal carries no datetime, so unlike /mistakes
    and /topics this route's body is a straight asdict() with nothing to
    isoformat()."""

    def test_should_return_200_with_total_seconds_and_session_count(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_speaking_total.return_value = SpeakingTotal(
            total_seconds=5400.0, session_count=3
        )

        # when
        response = client.get("/progress/speaking")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"total_seconds": 5400.0, "session_count": 3}
        mock_orchestrator.get_speaking_total.assert_called_once_with()

    def test_should_return_200_with_zeroes_when_nothing_logged(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_speaking_total.return_value = SpeakingTotal(total_seconds=0.0, session_count=0)

        # when
        response = client.get("/progress/speaking")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"total_seconds": 0.0, "session_count": 0}

    def test_should_return_500_when_orchestrator_raises_dependency_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_speaking_total.side_effect = ProgressOrchestrationDependencyException(
            inner_exception=RuntimeError("db down")
        )

        # when / then
        assert client.get("/progress/speaking").status_code == 500

    def test_should_return_500_when_orchestrator_raises_service_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_speaking_total.side_effect = ProgressOrchestrationServiceException(
            inner_exception=RuntimeError("unexpected")
        )

        # when / then
        assert client.get("/progress/speaking").status_code == 500


class TestGetStreak:
    """Roadmap C3."""

    def test_should_return_200_with_longest_and_current(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_longest_unflagged_streak.return_value = UnflaggedStreak(longest=4, current=1)

        # when
        response = client.get("/progress/streak")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"longest": 4, "current": 1}
        mock_orchestrator.get_longest_unflagged_streak.assert_called_once_with()

    def test_should_return_200_with_zeroes_when_nothing_logged(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_longest_unflagged_streak.return_value = UnflaggedStreak(longest=0, current=0)

        # when
        response = client.get("/progress/streak")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"longest": 0, "current": 0}

    def test_should_return_500_when_orchestrator_raises_dependency_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_longest_unflagged_streak.side_effect = ProgressOrchestrationDependencyException(
            inner_exception=RuntimeError("db down")
        )

        # when / then
        assert client.get("/progress/streak").status_code == 500

    def test_should_return_500_when_orchestrator_raises_service_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_longest_unflagged_streak.side_effect = ProgressOrchestrationServiceException(
            inner_exception=RuntimeError("unexpected")
        )

        # when / then
        assert client.get("/progress/streak").status_code == 500


class TestGetRecap:
    """Roadmap C2. Unlike /speaking and /streak, there is no zero-valued
    SessionRecap to fall back to -- the "nothing yet" case is `null`, not a
    dataclass of zeroes, so it gets its own explicit test rather than
    reusing the "zeroes when nothing logged" shape above."""

    def test_should_return_200_with_isoformat_timestamps_when_a_session_has_completed(
        self, client, mock_recap_aggregator
    ):
        # given
        mock_recap_aggregator.get_latest_recap.return_value = SessionRecap(
            flag_count=2,
            categories_flagged=["gender-agreement", "ser-vs-estar"],
            session_started_at=datetime(2026, 9, 18, 18, 0, 0),
            session_ended_at=datetime(2026, 9, 18, 18, 20, 0),
        )

        # when
        response = client.get("/progress/recap")

        # then
        assert response.status_code == 200
        assert response.get_json() == {
            "flag_count": 2,
            "categories_flagged": ["gender-agreement", "ser-vs-estar"],
            "session_started_at": "2026-09-18T18:00:00",
            "session_ended_at": "2026-09-18T18:20:00",
        }
        mock_recap_aggregator.get_latest_recap.assert_called_once_with()

    def test_should_return_200_with_null_when_no_session_has_ever_completed(self, client, mock_recap_aggregator):
        # given
        mock_recap_aggregator.get_latest_recap.return_value = None

        # when
        response = client.get("/progress/recap")

        # then
        assert response.status_code == 200
        assert response.get_json() is None

    def test_should_return_500_when_aggregator_raises_dependency_exception(self, client, mock_recap_aggregator):
        # given
        mock_recap_aggregator.get_latest_recap.side_effect = SessionRecapAggregationDependencyException(
            inner_exception=RuntimeError("db down")
        )

        # when / then
        assert client.get("/progress/recap").status_code == 500

    def test_should_return_500_when_aggregator_raises_service_exception(self, client, mock_recap_aggregator):
        # given
        mock_recap_aggregator.get_latest_recap.side_effect = SessionRecapAggregationServiceException(
            inner_exception=RuntimeError("unexpected")
        )

        # when / then
        assert client.get("/progress/recap").status_code == 500
