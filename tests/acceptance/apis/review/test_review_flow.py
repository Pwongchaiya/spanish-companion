"""Acceptance tests for the Review feature's HTTP round trip.

Per CLAUDE.md's Phase 2 test strategy: full Flask app in-process
(app.test_client()), real file-backed brokers behind real Foundation
services, pointed at pytest tmp_path (self-cleaning by construction),
external dependencies (Retrieval, Generation) mocked at their service
boundary. Does NOT go through api.app.create_app() -- that wires real
Postgres/Gemini brokers with no injection point, out of scope here.
Retrieval/Generation's own behavior is out of scope too; this tier is about
Review's real flagged-list -> selection -> explanation -> practice flow
against real JSON/JSONL files.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from flask import Flask

from api.brokers.flag import JsonFileFlagBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.practice_log import JsonLinesPracticeLogBroker
from api.exposers.review import make_review_blueprint
from api.models.foundations.flag import Flag
from api.models.foundations.learner_profile.learner_profile import LearnerProfile
from api.services.foundations.flag import FlagService
from api.services.foundations.practice_log import PracticeLogService
from api.services.orchestrations.review import ReviewOrchestrationService
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from api.services.processings.mistake_pattern import IMistakePatternProcessingService
from rag.models.foundations.generation import Explanation
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalOrchestrationService


@pytest.fixture
def seeded_flags():
    return [
        Flag(
            id="flag-1",
            said="yo soy tener",
            corrected="yo tengo",
            category="verb_conjugation",
            timestamp=datetime(2026, 8, 1, 12, 0, 0),
        ),
        Flag(
            id="flag-2",
            said="el mesa",
            corrected="la mesa",
            category="gender_agreement",
            timestamp=datetime(2026, 8, 1, 12, 5, 0),
        ),
    ]


@pytest.fixture
def flag_broker(tmp_path, seeded_flags):
    broker = JsonFileFlagBroker(path=tmp_path / "flags.json")
    broker.save_flags(seeded_flags)
    return broker


@pytest.fixture
def practice_log_broker(tmp_path):
    return JsonLinesPracticeLogBroker(path=tmp_path / "practice_log.jsonl")


@pytest.fixture
def flag_service(flag_broker):
    return FlagService(flag_broker=flag_broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def practice_log_service(practice_log_broker):
    return PracticeLogService(practice_log_broker=practice_log_broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def mock_retrieval_service():
    mock = Mock(spec=HybridRetrievalOrchestrationService)
    mock.retrieve.return_value = [
        ScoredChunk(
            chunk_id=1,
            topic="verb_conjugation",
            source_url="https://rae.es/verb-conjugation",
            content="El verbo 'tener' se conjuga como 'tengo' en la primera persona.",
            score=0.9,
        )
    ]
    return mock


@pytest.fixture
def mock_generation_service():
    mock = Mock(spec=GenerationService)
    mock.explain.return_value = Explanation(
        explanation="Use 'tengo' for the first person present of tener.",
        source_url="https://rae.es/verb-conjugation",
        source_excerpt="El verbo 'tener' se conjuga como 'tengo' en la primera persona.",
    )
    mock.judge_practice_attempt.return_value = True
    return mock


@pytest.fixture
def mock_learner_profile_processing_service():
    mock = Mock(spec=ILearnerProfileProcessingService)
    mock.ensure_profile.return_value = LearnerProfile(
        id=1, proficiency_level="beginner", updated_at=datetime(2026, 8, 1)
    )
    return mock


@pytest.fixture
def mock_mistake_pattern_processing_service():
    return Mock(spec=IMistakePatternProcessingService)


@pytest.fixture
def client(
    flag_service,
    practice_log_service,
    mock_retrieval_service,
    mock_generation_service,
    mock_learner_profile_processing_service,
    mock_mistake_pattern_processing_service,
):
    orchestrator = ReviewOrchestrationService(
        flag_service=flag_service,
        practice_log_service=practice_log_service,
        retrieval_service=mock_retrieval_service,
        generation_service=mock_generation_service,
        learner_profile_processing_service=mock_learner_profile_processing_service,
        mistake_pattern_processing_service=mock_mistake_pattern_processing_service,
        logging_broker=StdlibLoggingBroker(),
    )
    app = Flask(__name__)
    app.register_blueprint(make_review_blueprint(orchestrator))
    return app.test_client()


class TestListFlags:

    def test_should_return_seeded_flags(self, client, seeded_flags):
        # when
        response = client.get("/review/flags")

        # then
        assert response.status_code == 200
        body = response.get_json()
        assert [f["id"] for f in body] == [f.id for f in seeded_flags]
        assert body[0]["timestamp"] == seeded_flags[0].timestamp.isoformat()


class TestExplainFlag:

    def test_should_return_200_with_mocked_explanation_for_known_flag(self, client, mock_generation_service):
        # when
        response = client.get("/review/flags/flag-1/explain")

        # then
        assert response.status_code == 200
        assert response.get_json() == {
            "explanation": "Use 'tengo' for the first person present of tener.",
            "source_url": "https://rae.es/verb-conjugation",
            "source_excerpt": "El verbo 'tener' se conjuga como 'tengo' en la primera persona.",
        }

    def test_should_return_404_for_unknown_flag(self, client):
        # when
        response = client.get("/review/flags/does-not-exist/explain")

        # then
        assert response.status_code == 404
        assert "error" in response.get_json()


class TestRecordPractice:

    def test_should_persist_attempt_to_real_file_and_return_201(self, client, practice_log_broker):
        # when
        response = client.post("/review/flags/flag-1/practice", json={"attempt_text": "yo tengo"})

        # then -- HTTP response
        assert response.status_code == 201
        body = response.get_json()
        assert body["flag_id"] == "flag-1"
        assert body["attempt_text"] == "yo tengo"

        # then -- actually written to the real temp file, read back via the
        # same broker instance the app was built with
        persisted = practice_log_broker.read_attempts()
        assert len(persisted) == 1
        assert persisted[0].flag_id == "flag-1"
        assert persisted[0].attempt_text == "yo tengo"

    def test_should_return_404_for_unknown_flag(self, client):
        # when
        response = client.post("/review/flags/does-not-exist/practice", json={"attempt_text": "yo tengo"})

        # then
        assert response.status_code == 404
        assert "error" in response.get_json()
