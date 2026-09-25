"""Acceptance test for GET /progress/recap -- full HTTP round trip through
the real Exposer -> Aggregation -> (Progress Orchestration -> Foundation ->
Broker -> SQL) stack, with Review's flag list mocked (roadmap C2).

Same deliberate scope narrowing as test_speaking_and_streak.py, for the same
reason: not api.app.create_app() -- ReviewOrchestrationService pulls in
Azure/Gemini/retrieval credentials this route never touches.

Per CLAUDE.md's Phase 2 test strategy, this hits a real test Postgres
(TEST_DATABASE_URL, never DATABASE_URL) -- see tests/acceptance/conftest.py.
The session_log table is truncated in teardown; self-cleaning.

ReviewOrchestrationService is mocked at the Orchestration boundary (its
list_flags() is a Protocol method with no persistence of its own visible
from here) rather than built for real, since its own dependencies
(FlagBroker, retrieval, generation) have nothing to do with this route.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from flask import Flask

from api.brokers.logging import StdlibLoggingBroker
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.exposers.progress import make_progress_blueprint
from api.services.aggregations.session_recap import SessionRecapAggregationService
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.pronunciation_result import IPronunciationResultService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.progress import ProgressOrchestrationService
from api.services.orchestrations.review import ReviewService
from api.services.processings.learner_profile import ILearnerProfileProcessingService

SESSION_START = datetime(2026, 9, 18, 18, 0, 0)


@pytest.fixture
def session_log_entry_service(test_database_url, truncate_tables):
    truncate_tables("session_log")
    broker = SqlAlchemySessionLogEntryBroker(test_database_url)
    return SessionLogEntryService(broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def mock_review_service():
    return Mock(spec=ReviewService)


@pytest.fixture
def client(session_log_entry_service, mock_review_service):
    progress_orchestrator = ProgressOrchestrationService(
        Mock(spec=ILearnerProfileProcessingService),
        Mock(spec=IMistakePatternService),
        Mock(spec=ITopicCoveredService),
        session_log_entry_service,
        Mock(spec=IPronunciationResultService),
        logging_broker=StdlibLoggingBroker(),
    )
    recap_aggregator = SessionRecapAggregationService(
        mock_review_service,
        progress_orchestrator,
        Mock(),  # tts_service: /recap never synthesizes
        logging_broker=StdlibLoggingBroker(),
    )
    app = Flask(__name__)
    app.register_blueprint(make_progress_blueprint(progress_orchestrator, recap_aggregator))
    return app.test_client()


def _log_session(service, minutes: float | None, flag_count: int = 0):
    entry = service.create_session_log_entry(SESSION_START)
    if minutes is not None:
        service.complete_session_log_entry(entry.id, SESSION_START + timedelta(minutes=minutes), flag_count)
    return entry


class TestGetRecap:

    def test_returns_null_when_no_session_has_ever_completed(self, client):
        response = client.get("/progress/recap")

        assert response.status_code == 200
        assert response.get_json() is None

    def test_returns_the_latest_completed_sessions_recap(
        self, client, session_log_entry_service, mock_review_service
    ):
        _log_session(session_log_entry_service, minutes=20, flag_count=2)
        mock_review_service.list_flags.return_value = [
            Mock(category="ser-vs-estar"),
            Mock(category="gender-agreement"),
        ]

        response = client.get("/progress/recap")

        assert response.status_code == 200
        assert response.get_json() == {
            "flag_count": 2,
            "categories_flagged": ["gender-agreement", "ser-vs-estar"],
            "session_started_at": SESSION_START.isoformat(),
            "session_ended_at": (SESSION_START + timedelta(minutes=20)).isoformat(),
        }

    def test_ignores_a_still_running_session_and_falls_back_to_null(
        self, client, session_log_entry_service
    ):
        _log_session(session_log_entry_service, minutes=None)

        response = client.get("/progress/recap")

        assert response.status_code == 200
        assert response.get_json() is None
