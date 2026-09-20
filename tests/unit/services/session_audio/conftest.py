"""Shared fixtures for SessionAudioService unit tests.

The broker is mocked via Mock(spec=ISessionAudioBroker). Every datetime is a
fixed literal -- no datetime.now().
"""

from dataclasses import replace
from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.session_audio import ISessionAudioBroker
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.services.foundations.session_audio import SessionAudioService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_TIME = datetime(2026, 1, 2, 10, 0, 0)


@pytest.fixture
def mock_session_audio_broker():
    return Mock(spec=ISessionAudioBroker)


@pytest.fixture
def service(mock_session_audio_broker, mock_logging_broker):
    return SessionAudioService(mock_session_audio_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def make_session_audio():
    def _make(**overrides) -> SessionAudio:
        base = SessionAudio(
            id=None, session_log_id=4, file_path="data/audio/session_4.wav", duration_seconds=61.5, created_at=FIXED_TIME
        )
        return replace(base, **overrides)

    return _make
