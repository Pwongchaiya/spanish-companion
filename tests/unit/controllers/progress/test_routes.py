"""Unit tests for the Progress blueprint's HTTP mapping.

Per CLAUDE.md's Phase 2 test strategy: this tier verifies HTTP mapping only
(status codes, JSON shape, isoformat timestamps) -- never Progress's actual
read logic. ProgressOrchestrationService is mocked via
unittest.mock.Mock(spec=ProgressOrchestrationService);
tests/unit/services/progress/ covers the real logic.

Both routes take no input, so there is no validation-shaped 400 case --
same two-tier exception mapping (Dependency/Service only) as Review's
GET /review/flags.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from flask import Flask

from api.exposers.progress import make_progress_blueprint
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
)
from api.models.orchestrations.progress.topic_coverage_entry import TopicCoverageEntry
from api.services.orchestrations.progress import ProgressOrchestrationService


@pytest.fixture
def mock_orchestrator():
    return Mock(spec=ProgressOrchestrationService)


@pytest.fixture
def client(mock_orchestrator):
    app = Flask(__name__)
    app.register_blueprint(make_progress_blueprint(mock_orchestrator))
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
