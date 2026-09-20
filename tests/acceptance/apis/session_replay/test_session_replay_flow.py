"""Acceptance tests for E3 transcript replay's HTTP round trip.

Per CLAUDE.md's Phase 2 test strategy: Flask app in-process (app.test_client()),
real brokers behind real Foundation/Orchestration services, pointed at pytest
tmp_path (self-cleaning by construction): file-backed sqlite stands in for the
test Postgres, a real WAV lands in tmp_path, flags come from a real JSON file.
No external API is involved. Not api.app.create_app() -- it wires real
Postgres/Azure/Gemini brokers with no injection point (same as the other
acceptance tiers here); the Origin/Referer allowlist it applies is exercised via
the same api.app helpers. Round trip: record -> replay -> audio -> prune.
"""

from datetime import datetime

import pytest
from flask import Flask, jsonify, request
from sqlalchemy import create_engine

from api.app import ALLOWED_ORIGINS, _is_allowed_origin
from api.brokers.audio_storage import LocalWavAudioStorageBroker
from api.brokers.flag import JsonFileFlagBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.session_audio import SqlAlchemySessionAudioBroker
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.exposers.session_replay import make_session_replay_blueprint
from api.models.base import Base
from api.models.foundations.flag import Flag
from api.models.foundations.session_audio.session_audio import SessionAudioRecord
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntryRecord
from api.services.foundations.audio_storage import AudioStorageService
from api.services.foundations.flag import FlagService
from api.services.foundations.session_audio import SessionAudioService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.orchestrations.session_audio_recording import SessionAudioRecordingOrchestrationService
from api.services.orchestrations.session_replay import SessionReplayOrchestrationService

START = datetime(2026, 3, 1, 10, 0, 0)
END = datetime(2026, 3, 1, 10, 1, 0)
NOW = datetime(2026, 3, 1, 10, 2, 0)


@pytest.fixture
def stack(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine, tables=[SessionLogEntryRecord.__table__, SessionAudioRecord.__table__])
    engine.dispose()
    logging_broker = StdlibLoggingBroker()

    entries = SessionLogEntryService(SqlAlchemySessionLogEntryBroker(url), logging_broker=logging_broker)
    session_audio = SessionAudioService(SqlAlchemySessionAudioBroker(url), logging_broker=logging_broker)
    storage = AudioStorageService(LocalWavAudioStorageBroker(tmp_path / "audio"), logging_broker=logging_broker)
    flag_broker = JsonFileFlagBroker(path=tmp_path / "flags.json")
    flag_broker.save_flags(
        [
            Flag("f-in", "yo tiene", "yo tengo", "conjugation", datetime(2026, 3, 1, 10, 0, 20)),
            Flag("f-other-session", "el mesa", "la mesa", "gender", datetime(2026, 2, 1, 9, 0, 0)),
        ]
    )
    recording = SessionAudioRecordingOrchestrationService(storage, session_audio, lambda: NOW, logging_broker=logging_broker)
    replay = SessionReplayOrchestrationService(
        session_audio, FlagService(flag_broker, logging_broker=logging_broker), entries, logging_broker=logging_broker
    )
    entry = entries.create_session_log_entry(START, None)
    entries.complete_session_log_entry(entry.id, END, 1)

    app = Flask(__name__)

    @app.before_request
    def check_origin():  # same rule api/app.py's create_app applies app-wide
        header = request.headers.get("Origin") or request.headers.get("Referer")
        if header is not None and not _is_allowed_origin(header, ALLOWED_ORIGINS):
            return jsonify({"error": "origin not allowed"}), 403
        return None

    app.register_blueprint(make_session_replay_blueprint(replay))
    return app.test_client(), recording, entry.id, tmp_path


def test_record_then_replay_then_stream_audio(stack):
    client, recording, session_id, _ = stack
    pcm = b"\x01\x00" * (24000 * 30)  # 30s mono 24kHz (flag sits 20s in)
    recording.save_recording(session_id, pcm, 24000, 1)

    body = client.get(f"/review/sessions/{session_id}/replay").get_json()

    assert body == {
        "session_log_id": session_id,
        "duration_seconds": 30.0,
        "audio_url": f"/review/sessions/{session_id}/audio",
        "flags": [
            {
                "flag_id": "f-in",
                "offset_seconds": 20.0,
                "said": "yo tiene",
                "corrected": "yo tengo",
                "category": "conjugation",
            }
        ],
    }
    audio = client.get(body["audio_url"])
    assert audio.status_code == 200 and audio.mimetype == "audio/wav"
    assert audio.data[:4] == b"RIFF" and audio.data[8:12] == b"WAVE"
    assert client.get(body["audio_url"], headers={"Range": "bytes=0-99"}).status_code == 206


def test_should_return_404_for_a_session_with_no_recording(stack):
    client, _, session_id, _ = stack

    assert client.get(f"/review/sessions/{session_id}/replay").status_code == 404
    assert client.get(f"/review/sessions/{session_id}/audio").status_code == 404


def test_should_return_404_for_an_unknown_session(stack):
    client, recording, session_id, _ = stack
    recording.save_recording(session_id, b"\x01\x00" * 100, 24000, 1)

    assert client.get("/review/sessions/999/replay").status_code == 404


def test_routes_should_reject_a_disallowed_origin_and_allow_a_local_one(stack):
    client, recording, session_id, _ = stack
    recording.save_recording(session_id, b"\x01\x00" * 100, 24000, 1)

    for route in ("replay", "audio"):
        url = f"/review/sessions/{session_id}/{route}"
        assert client.get(url, headers={"Origin": "http://evil.example"}).status_code == 403
        assert client.get(url, headers={"Origin": "http://localhost:5173"}).status_code == 200


def test_prune_should_remove_expired_file_and_row_so_replay_404s(stack):
    client, recording, session_id, tmp_path = stack
    row = recording.save_recording(session_id, b"\x01\x00" * 100, 24000, 1)

    assert recording.prune_expired(30) == 0  # created NOW, well inside retention
    assert (tmp_path / "audio" / "session_1.wav").exists()

    # fixed clock is NOW; ask for a 0-day window after time has "passed" by using a later clock
    later = SessionAudioRecordingOrchestrationService(
        recording._audio_storage_service,
        recording._session_audio_service,
        lambda: datetime(2026, 5, 1),
        logging_broker=StdlibLoggingBroker(),
    )
    assert later.prune_expired(30) == 1
    assert not (tmp_path / "audio" / "session_1.wav").exists()
    assert client.get(f"/review/sessions/{session_id}/audio").status_code == 404
    assert row.id is not None
