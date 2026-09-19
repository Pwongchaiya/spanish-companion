"""Acceptance tests for GET /progress/speaking and GET /progress/streak --
full HTTP round trip through the real Exposer -> Orchestration ->
Foundation -> Broker -> SQL stack (roadmap C1/C3).

Two deliberate deviations from CLAUDE.md's acceptance-tier definition, both
narrowing scope rather than widening it:

1. Not api.app.create_app(). Same reason the session_lifecycle acceptance
   test builds its own Flask app: create_app() wires a real
   SubprocessBotProcessBroker at the real voice bot and requires Azure/
   Gemini credentials, none of which these two read-only routes touch.

2. sqlite, not a test Postgres. These rows use no pgvector, no Postgres
   type, and no constraint sqlite lacks -- the 0003 migration's own
   self-check makes the same call for the same reason. What this tier is
   actually here to catch is wiring the four layers cannot check
   individually: route registration, dependency order at construction, and
   dataclass -> JSON shape. A live Postgres would not catch more of that.
   The three A5/F1 dependencies are mocked out; they have their own suites
   and neither route under test reads them.

Self-cleaning: each test gets its own in-memory engine, so there is nothing
to tear down.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from flask import Flask

from api.brokers.logging import StdlibLoggingBroker
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.exposers.progress import make_progress_blueprint
from api.models.base import Base
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntryRecord
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.progress import ProgressOrchestrationService
from api.services.processings.learner_profile import ILearnerProfileProcessingService

SESSION_START = datetime(2026, 9, 1, 18, 0, 0)


@pytest.fixture
def session_log_entry_service():
    broker = SqlAlchemySessionLogEntryBroker("sqlite://")
    Base.metadata.create_all(broker._engine, tables=[SessionLogEntryRecord.__table__])
    return SessionLogEntryService(broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def client(session_log_entry_service):
    orchestrator = ProgressOrchestrationService(
        Mock(spec=ILearnerProfileProcessingService),
        Mock(spec=IMistakePatternService),
        Mock(spec=ITopicCoveredService),
        session_log_entry_service,
        logging_broker=StdlibLoggingBroker(),
    )
    app = Flask(__name__)
    app.register_blueprint(make_progress_blueprint(orchestrator))
    return app.test_client()


def _log_session(service, day_offset: int, minutes: int | None, flag_count: int = 0):
    """Write one session the way the voice loop does: create on start, then
    complete on stop -- or leave it open, if minutes is None."""
    started_at = SESSION_START + timedelta(days=day_offset)
    entry = service.create_session_log_entry(started_at)
    if minutes is not None:
        service.complete_session_log_entry(entry.id, started_at + timedelta(minutes=minutes), flag_count)
    return entry


class TestSpeakingTotal:

    def test_returns_zeroes_before_any_session_exists(self, client):
        response = client.get("/progress/speaking")

        assert response.status_code == 200
        assert response.get_json() == {"total_seconds": 0.0, "session_count": 0}

    def test_sums_completed_sessions_and_ignores_an_open_one(self, client, session_log_entry_service):
        _log_session(session_log_entry_service, 0, minutes=30)
        _log_session(session_log_entry_service, 1, minutes=20)
        _log_session(session_log_entry_service, 2, minutes=None)  # still running

        response = client.get("/progress/speaking")

        assert response.status_code == 200
        assert response.get_json() == {"total_seconds": 50 * 60, "session_count": 2}


class TestUnflaggedStreak:

    def test_returns_zeroes_before_any_session_exists(self, client):
        response = client.get("/progress/streak")

        assert response.status_code == 200
        assert response.get_json() == {"longest": 0, "current": 0}

    def test_counts_clean_sessions_in_start_order(self, client, session_log_entry_service):
        # 0, 0, 0, 2, 0 -> best run of 3, currently 1
        for day, flags in enumerate([0, 0, 0, 2, 0]):
            _log_session(session_log_entry_service, day, minutes=10, flag_count=flags)

        response = client.get("/progress/streak")

        assert response.status_code == 200
        assert response.get_json() == {"longest": 3, "current": 1}

    def test_an_open_session_does_not_extend_the_streak(self, client, session_log_entry_service):
        # An open row still carries its insert-time flag_count of 0. If it
        # leaked into the fold it would report current=3 instead of 2.
        _log_session(session_log_entry_service, 0, minutes=10, flag_count=0)
        _log_session(session_log_entry_service, 1, minutes=10, flag_count=0)
        _log_session(session_log_entry_service, 2, minutes=None)

        response = client.get("/progress/streak")

        assert response.get_json() == {"longest": 2, "current": 2}
