"""Shared fixtures for LearnerProfileOrchestrationService unit tests.

Per CLAUDE.md's Phase 2 test strategy: all four dependencies are mocked via
unittest.mock.Mock(spec=...) at their Protocol boundary -- never the real
Processing/Foundation collaborators, which would drag in Postgres.
ConfigurationBroker is faked (FakeConfigurationBroker) rather than reading
real env vars, same pattern as tests/unit/services/review/conftest.py.

Does not collide with test_learner_profile_service.py /
test_learner_profile_processing_service.py in this same directory -- both
are plain fixture-free functions, so this conftest.py adds fixtures without
touching them.
"""

from datetime import datetime

from unittest.mock import Mock

import pytest

from api.models.foundations.flag import Flag
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.foundations.topic_covered.topic_covered import TopicCovered
from api.services.foundations.flag import IFlagService
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.learner_profile.learner_profile_orchestration_service import (
    LearnerProfileOrchestrationService,
)
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
def mock_flag_service():
    return Mock(spec=IFlagService)


@pytest.fixture
def configuration_broker():
    return FakeConfigurationBroker({"DEFAULT_PROFICIENCY_LEVEL": "beginner", "RECENT_FLAG_LIMIT": "5"})


@pytest.fixture
def service(
    mock_learner_profile_processing_service,
    mock_mistake_pattern_service,
    mock_topic_covered_service,
    mock_flag_service,
    configuration_broker,
    mock_logging_broker,
):
    return LearnerProfileOrchestrationService(
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        mock_flag_service,
        logging_broker=mock_logging_broker,
        configuration_broker=configuration_broker,
    )


# Factories are fixtures, not module-level functions, matching the review
# conftest.py precedent -- keeps every sibling conftest.py import-safe under
# pytest's default prepend sys.path mode.
@pytest.fixture
def make_profile():
    def _make(profile_id: int = 1, proficiency_level: str | None = "beginner") -> LearnerProfile:
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
    def _make(
        topic_id: int = 1,
        profile_id: int = 1,
        topic: str = "past_tense",
        last_practiced_at: datetime = FIXED_NOW,
    ) -> TopicCovered:
        return TopicCovered(
            id=topic_id,
            profile_id=profile_id,
            topic=topic,
            first_covered_at=FIXED_NOW,
            last_practiced_at=last_practiced_at,
        )

    return _make


@pytest.fixture
def make_flag():
    def _make(flag_id: str = "flag-1", category: str = "preterite", timestamp: datetime = FIXED_NOW) -> Flag:
        return Flag(id=flag_id, said="iba", corrected="fui", category=category, timestamp=timestamp)

    return _make
