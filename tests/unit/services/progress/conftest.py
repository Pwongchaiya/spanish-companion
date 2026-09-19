"""Shared fixtures for ProgressOrchestrationService unit tests.

Per CLAUDE.md's Phase 2 test strategy: all three dependencies are mocked via
unittest.mock.Mock(spec=...) at their Protocol boundary -- never the real
Processing/Foundation collaborators, which would drag in Postgres.
ConfigurationBroker is faked (FakeConfigurationBroker), same pattern as
tests/unit/services/learner_profile/conftest.py.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.progress.progress_service import ProgressOrchestrationService
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_NOW = datetime(2026, 1, 2, 3, 4, 5)


class FakeConfigurationBroker:
    """Dict-backed ConfigurationBroker stub -- fixed, known config values."""

    def __init__(self, values: dict) -> None:
        self._values = values

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._values.get(key, default)

    def require(self, key: str) -> str:
        return self._values[key]


@pytest.fixture
def mock_learner_profile_processing_service():
    return Mock(spec=ILearnerProfileProcessingService)


@pytest.fixture
def mock_mistake_pattern_service():
    return Mock(spec=IMistakePatternService)


@pytest.fixture
def mock_topic_covered_service():
    return Mock(spec=ITopicCoveredService)


@pytest.fixture
def mock_session_log_entry_service():
    return Mock(spec=ISessionLogEntryService)


@pytest.fixture
def configuration_broker():
    return FakeConfigurationBroker({"DEFAULT_PROFICIENCY_LEVEL": "beginner"})


@pytest.fixture
def service(
    mock_learner_profile_processing_service,
    mock_mistake_pattern_service,
    mock_topic_covered_service,
    mock_session_log_entry_service,
    configuration_broker,
    mock_logging_broker,
):
    return ProgressOrchestrationService(
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_session_log_entry_service,
        logging_broker=mock_logging_broker,
        configuration_broker=configuration_broker,
    )


@pytest.fixture
def make_profile():
    from api.models.foundations.learner_profile.learner_profile import LearnerProfile

    def _make(profile_id: int = 1, proficiency_level: str | None = "beginner"):
        return LearnerProfile(id=profile_id, proficiency_level=proficiency_level, updated_at=FIXED_NOW)

    return _make


@pytest.fixture
def make_pattern():
    def _make(
        pattern_id: int = 1,
        profile_id: int = 1,
        category: str = "ser_estar",
        occurrence_count: int = 1,
        status: str = "active",
    ) -> MistakePattern:
        return MistakePattern(
            id=pattern_id,
            profile_id=profile_id,
            category=category,
            occurrence_count=occurrence_count,
            last_seen_at=FIXED_NOW,
            status=status,
        )

    return _make


@pytest.fixture
def make_topic():
    def _make(topic_id: int = 1, profile_id: int = 1, topic: str = "ser-vs-estar") -> TopicCovered:
        return TopicCovered(
            id=topic_id,
            profile_id=profile_id,
            topic=topic,
            first_covered_at=FIXED_NOW,
            last_practiced_at=FIXED_NOW,
        )

    return _make


@pytest.fixture
def make_session():
    """A completed session_log row, unless ended_at is explicitly None.

    Default duration is 30 minutes, so a test asserting on total seconds
    reads as "n sessions x 1800s" without restating the arithmetic.
    """

    def _make(
        entry_id: int = 1,
        started_at: datetime = FIXED_NOW,
        minutes: float | None = 30.0,
        flag_count: int = 0,
    ) -> SessionLogEntry:
        return SessionLogEntry(
            id=entry_id,
            started_at=started_at,
            ended_at=None if minutes is None else started_at + timedelta(minutes=minutes),
            flag_count=flag_count,
        )

    return _make
