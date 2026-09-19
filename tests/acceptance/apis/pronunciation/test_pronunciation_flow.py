"""Acceptance tests for POST /pronunciation/assess and GET /progress/pronunciation --
full HTTP round trip through the real Exposer -> Orchestration -> Foundation -> Broker stack.

Same two narrowings as tests/acceptance/apis/progress/test_speaking_and_streak.py, for the same
reasons: a bare Flask app (create_app() needs Azure/Gemini/Postgres), and in-memory sqlite for the
pronunciation_result table. The Azure assessment broker is a Mock -- no live SDK call. The 413 cap
is applied through api.app._register_upload_limit, the same function create_app() calls.

Self-cleaning: each test gets its own in-memory engine.
"""

import io
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from flask import Flask

from api.app import MAX_UPLOAD_BYTES, _register_upload_limit
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.pronunciation_assessment import PronunciationAssessmentBroker
from api.brokers.pronunciation_result import SqlAlchemyPronunciationResultBroker
from api.exposers.progress import make_progress_blueprint
from api.exposers.pronunciation import make_pronunciation_blueprint
from api.models.base import Base
from api.models.foundations.pronunciation_assessment.pronunciation_assessment import (
    PhonemeScore,
    PronunciationAssessment,
    WordScore,
)
from api.models.foundations.pronunciation_result.pronunciation_result import (
    PronunciationResult,
    PronunciationResultRecord,
)
from api.services.aggregations.session_recap import SessionRecapAggregationService
from api.services.foundations.mistake_pattern import IMistakePatternService
from api.services.foundations.pronunciation_assessment import PronunciationAssessmentService
from api.services.foundations.pronunciation_result import PronunciationResultService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.foundations.topic_covered import ITopicCoveredService
from api.services.orchestrations.progress import ProgressOrchestrationService
from api.services.orchestrations.pronunciation import PronunciationOrchestrationService, PronunciationService
from api.services.orchestrations.review import ReviewService
from api.services.processings.learner_profile import ILearnerProfileProcessingService

NOW = datetime(2026, 9, 1, 18, 0, 0)
WAV = b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x00" * 40


@pytest.fixture
def assessment_broker():
    broker = Mock(spec=PronunciationAssessmentBroker)
    broker.assess.return_value = PronunciationAssessment(
        accuracy_score=90.0,
        fluency_score=80.0,
        completeness_score=100.0,
        pronunciation_score=88.0,
        prosody_score=None,
        words=[WordScore("perro", 90.0, "None", [PhonemeScore("p", 95.0)])],
    )
    return broker


@pytest.fixture
def result_service():
    broker = SqlAlchemyPronunciationResultBroker("sqlite://")
    Base.metadata.create_all(broker._engine, tables=[PronunciationResultRecord.__table__])
    return PronunciationResultService(broker, logging_broker=StdlibLoggingBroker())


@pytest.fixture
def client(assessment_broker, result_service):
    logging_broker = StdlibLoggingBroker()
    orchestrator = PronunciationOrchestrationService(
        PronunciationAssessmentService(assessment_broker, logging_broker=logging_broker),
        result_service,
        clock=lambda: NOW,
        logging_broker=logging_broker,
    )
    progress = ProgressOrchestrationService(
        Mock(spec=ILearnerProfileProcessingService),
        Mock(spec=IMistakePatternService),
        Mock(spec=ITopicCoveredService),
        Mock(spec=ISessionLogEntryService),
        result_service,
        logging_broker=logging_broker,
    )
    recap = SessionRecapAggregationService(Mock(spec=ReviewService), progress, Mock(), logging_broker=logging_broker)
    app = Flask(__name__)
    _register_upload_limit(app)
    app.register_blueprint(make_pronunciation_blueprint(orchestrator))
    app.register_blueprint(make_progress_blueprint(progress, recap))
    return app.test_client()


def _post(client, audio: bytes | None = WAV, reference_text: str | None = "perro", headers=None):
    data = {}
    if audio is not None:
        data["audio"] = (io.BytesIO(audio), "clip.wav")
    if reference_text is not None:
        data["reference_text"] = reference_text
    return client.post("/pronunciation/assess", data=data, content_type="multipart/form-data", headers=headers)


class TestAssessPronunciation:

    def test_should_return_200_with_exact_shape_and_persist(self, client, assessment_broker):
        # when
        response = _post(client)

        # then
        assert response.status_code == 200
        assert response.get_json() == {
            "reference_text": "perro",
            "accuracy": 90.0,
            "fluency": 80.0,
            "completeness": 100.0,
            "prosody": None,
            "overall": 88.0,
            "words": [
                {
                    "word": "perro",
                    "accuracy": 90.0,
                    "error_type": "None",
                    "phonemes": [{"phoneme": "p", "accuracy": 95.0}],
                }
            ],
            "created_at": NOW.isoformat(),
        }
        assessment_broker.assess.assert_called_once_with(WAV, "perro")
        assert len(client.get("/progress/pronunciation").get_json()) == 1

    def test_should_allow_multipart_post_from_an_allowed_origin_header(self, client):
        # Origin/Referer is enforced only in create_app()'s before_request, which never reads the body;
        # a browser multipart POST carries Origin of the page, so it passes the same allowlist check.
        from api.app import ALLOWED_ORIGINS, _is_allowed_origin

        assert _is_allowed_origin("http://localhost:5173", ALLOWED_ORIGINS) is True
        assert _post(client, headers={"Origin": "http://localhost:5173"}).status_code == 200

    @pytest.mark.parametrize(
        "audio, reference_text",
        [
            (None, "perro"),
            (b"", "perro"),
            (b"RIFF" + b"\x00" * 40, "perro"),  # exactly 44 bytes
            (b"X" * 100, "perro"),  # not RIFF/WAVE
            (WAV, None),
            (WAV, "   "),
            (WAV, "a" * 201),
        ],
        ids=["no-audio", "empty-audio", "header-only", "not-wav", "no-text", "blank-text", "text-too-long"],
    )
    def test_should_return_400_without_touching_the_assessment_broker(
        self, client, assessment_broker, audio, reference_text
    ):
        # when
        response = _post(client, audio=audio, reference_text=reference_text)

        # then
        assert response.status_code == 400
        assert "error" in response.get_json()
        assessment_broker.assess.assert_not_called()

    def test_should_return_400_when_wav_exceeds_service_limit_but_fits_request_cap(self, client, assessment_broker):
        # given -- over the Foundation service's 1 MiB WAV cap, under the 2 MiB request cap
        big = WAV + b"\x00" * (1_048_576 + 1)

        # when
        response = _post(client, audio=big)

        # then
        assert response.status_code == 400
        assessment_broker.assess.assert_not_called()

    def test_should_return_413_json_when_request_exceeds_cap(self, client, assessment_broker):
        # given
        oversize = WAV + b"\x00" * MAX_UPLOAD_BYTES

        # when
        response = _post(client, audio=oversize)

        # then
        assert response.status_code == 413
        assert "error" in response.get_json()
        assessment_broker.assess.assert_not_called()

    def test_should_return_500_when_azure_is_unavailable(self, client, assessment_broker):
        # given
        assessment_broker.assess.side_effect = RuntimeError("azure down")

        # when
        response = _post(client)

        # then
        assert response.status_code == 500
        assert "error" in response.get_json()


class TestPronunciationTrend:

    def test_should_return_empty_list_when_nothing_scored(self, client):
        response = client.get("/progress/pronunciation")

        assert response.status_code == 200
        assert response.get_json() == []

    def test_should_return_populated_trend_oldest_to_newest(self, client, result_service):
        # given
        for i in range(3):
            result_service.create_pronunciation_result(
                PronunciationResult(
                    id=None,
                    created_at=NOW + timedelta(days=i),
                    reference_text="perro",
                    accuracy_score=10.0 * (i + 1),
                    fluency_score=20.0 * (i + 1),
                    completeness_score=100.0,
                    pronunciation_score=30.0 * (i + 1),
                    prosody_score=None,
                    words_json=[],
                    locale="es-ES",
                )
            )

        # when
        response = client.get("/progress/pronunciation")

        # then
        assert response.status_code == 200
        assert response.get_json() == [
            {
                "created_at": (NOW + timedelta(days=i)).isoformat(),
                "accuracy": 10.0 * (i + 1),
                "fluency": 20.0 * (i + 1),
                "overall": 30.0 * (i + 1),
            }
            for i in range(3)
        ]


class TestRouteValidationBeforeOrchestrator:

    @pytest.mark.parametrize(
        "audio, reference_text",
        [(None, "perro"), (b"X" * 100, "perro"), (WAV, "  "), (WAV, "a" * 201)],
        ids=["no-audio", "not-wav", "blank-text", "text-too-long"],
    )
    def test_should_not_call_orchestrator_on_bad_body(self, audio, reference_text):
        # given
        orchestrator = Mock(spec=PronunciationService)
        app = Flask(__name__)
        app.register_blueprint(make_pronunciation_blueprint(orchestrator))

        # when
        response = _post(app.test_client(), audio=audio, reference_text=reference_text)

        # then
        assert response.status_code == 400
        orchestrator.assess_and_record.assert_not_called()
