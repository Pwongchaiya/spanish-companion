"""Route tests for the session replay blueprint: exact JSON contract, status
mapping, and audio streaming. The orchestrator is Mock(spec=ISessionReplayService)."""

import wave
from datetime import datetime
from unittest.mock import Mock

import pytest
from flask import Flask

from api.exposers.session_replay import make_session_replay_blueprint
from api.models.foundations.session_audio.exceptions import (
    InvalidSessionAudioException,
    NotFoundSessionAudioException,
    SessionAudioDependencyException,
    SessionAudioValidationException,
)
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.models.orchestrations.session_replay.exceptions import (
    FailedSessionReplayOrchestrationServiceException,
    NotFoundSessionReplayException,
    SessionReplayOrchestrationDependencyException,
    SessionReplayOrchestrationServiceException,
    SessionReplayOrchestrationValidationException,
)
from api.models.orchestrations.session_replay.session_replay import ReplayFlag, SessionReplay
from api.services.orchestrations.session_replay import ISessionReplayService


@pytest.fixture
def orchestrator():
    return Mock(spec=ISessionReplayService)


@pytest.fixture
def client(orchestrator):
    app = Flask(__name__)
    app.register_blueprint(make_session_replay_blueprint(orchestrator))
    return app.test_client()


def test_replay_should_return_the_pinned_contract(client, orchestrator):
    orchestrator.get_replay.return_value = SessionReplay(
        4, 300.0, [ReplayFlag("f1", 12.5, "yo tiene", "yo tengo", "conjugation")]
    )

    response = client.get("/review/sessions/4/replay")

    assert response.status_code == 200
    assert response.get_json() == {
        "session_log_id": 4,
        "duration_seconds": 300.0,
        "audio_url": "/review/sessions/4/audio",
        "flags": [
            {
                "flag_id": "f1",
                "offset_seconds": 12.5,
                "said": "yo tiene",
                "corrected": "yo tengo",
                "category": "conjugation",
                "status": "open",
            }
        ],
    }
    orchestrator.get_replay.assert_called_once_with(4)


@pytest.mark.parametrize(
    "leaf_wrapper",
    [
        SessionAudioValidationException(inner_exception=NotFoundSessionAudioException()),
        NotFoundSessionReplayException(),
    ],
)
def test_replay_should_return_404_for_either_not_found_depth(client, orchestrator, leaf_wrapper):
    orchestrator.get_replay.side_effect = SessionReplayOrchestrationValidationException(inner_exception=leaf_wrapper)

    assert client.get("/review/sessions/4/replay").status_code == 404
    assert orchestrator.get_replay.call_count == 1


def test_replay_should_return_400_for_other_validation_failures(client, orchestrator):
    orchestrator.get_replay.side_effect = SessionReplayOrchestrationValidationException(
        inner_exception=SessionAudioValidationException(inner_exception=InvalidSessionAudioException())
    )

    assert client.get("/review/sessions/4/replay").status_code == 400


@pytest.mark.parametrize(
    "error",
    [
        SessionReplayOrchestrationDependencyException(
            inner_exception=SessionAudioDependencyException(inner_exception=OSError("db"))
        ),
        SessionReplayOrchestrationServiceException(
            inner_exception=FailedSessionReplayOrchestrationServiceException(inner_exception=RuntimeError("x"))
        ),
    ],
)
def test_replay_should_return_500_for_dependency_and_service_failures(client, orchestrator, error):
    orchestrator.get_replay.side_effect = error

    assert client.get("/review/sessions/4/replay").status_code == 500


def test_non_integer_session_id_should_not_match_a_route(client, orchestrator):
    assert client.get("/review/sessions/abc/replay").status_code == 404
    assert orchestrator.get_replay.call_count == 0


def test_audio_should_stream_the_wav(client, orchestrator, tmp_path):
    path = tmp_path / "s4.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\x00\x00" * 240)
    orchestrator.get_audio.return_value = SessionAudio(1, 4, str(path), 0.01, datetime(2026, 3, 1))

    response = client.get("/review/sessions/4/audio")

    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    assert response.data == path.read_bytes()
    orchestrator.get_audio.assert_called_once_with(4)


def test_audio_should_return_404_when_no_recording(client, orchestrator):
    orchestrator.get_audio.side_effect = SessionReplayOrchestrationValidationException(
        inner_exception=SessionAudioValidationException(inner_exception=NotFoundSessionAudioException())
    )

    assert client.get("/review/sessions/4/audio").status_code == 404


def test_audio_should_return_404_when_row_exists_but_file_is_gone(client, orchestrator, tmp_path):
    orchestrator.get_audio.return_value = SessionAudio(
        1, 4, str(tmp_path / "gone.wav"), 1.0, datetime(2026, 3, 1)
    )

    assert client.get("/review/sessions/4/audio").status_code == 404


def test_latest_should_return_the_newest_session_id(client, orchestrator):
    orchestrator.get_latest_session_id.return_value = 6

    response = client.get("/review/sessions/latest")

    assert response.status_code == 200 and response.get_json() == {"session_log_id": 6}
    assert orchestrator.get_latest_session_id.call_count == 1


def test_latest_should_return_404_when_nothing_recorded(client, orchestrator):
    orchestrator.get_latest_session_id.side_effect = SessionReplayOrchestrationValidationException(
        inner_exception=SessionAudioValidationException(inner_exception=NotFoundSessionAudioException())
    )

    assert client.get("/review/sessions/latest").status_code == 404
