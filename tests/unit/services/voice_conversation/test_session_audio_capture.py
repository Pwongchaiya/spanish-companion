"""E3 audio capture wiring on ConversationOrchestrationService: opt-in gating of the
AudioBufferProcessor, the on_audio_data handler, and best-effort teardown save.
No pipecat pipeline is run and no real audio is captured (needs a manual mic test)."""

import asyncio
from datetime import datetime
from unittest.mock import Mock

import pytest
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor

from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.services.orchestrations.session_audio_recording import ISessionAudioRecordingService
from api.services.orchestrations.voice_conversation.voice_conversation_service import (
    ConversationOrchestrationService,
)

ENTRY = SessionLogEntry(4, datetime(2026, 3, 1, 10, 0, 0), None, 0)


def _make(enabled="1", with_service=True):
    config = {"AUDIO_RECORD_ENABLED": enabled} if enabled is not None else {}
    return ConversationOrchestrationService(
        stt_broker=Mock(),
        transport=Mock(),
        tts=Mock(),
        llm=Mock(),
        session_log_service=Mock(),
        live_transcript_service=Mock(),
        flag_service=Mock(),
        session_log_broker=Mock(),
        session_log_entry_service=Mock(),
        generation_service=Mock(),
        learner_profile_processing_service=Mock(),
        learner_profile_service=Mock(),
        logging_broker=Mock(),
        configuration_broker=Mock(get=Mock(side_effect=lambda k, d=None: config.get(k, d))),
        session_audio_recording_service=Mock(spec=ISessionAudioRecordingService) if with_service else None,
    )


class TestBuildAudioBuffer:

    @pytest.mark.parametrize("enabled", [None, "0", "", "off"])
    def test_should_return_none_when_disabled(self, enabled):
        assert _make(enabled=enabled)._build_audio_buffer() is None

    def test_should_return_none_when_no_recording_service_wired(self):
        assert _make(enabled="1", with_service=False)._build_audio_buffer() is None

    @pytest.mark.parametrize("enabled", ["1", "true", "YES"])
    def test_should_return_buffer_when_enabled(self, enabled):
        assert isinstance(_make(enabled=enabled)._build_audio_buffer(), AudioBufferProcessor)

    def test_handler_should_hold_the_audio_for_teardown(self):
        s = _make()
        buffer = s._build_audio_buffer()
        handler = buffer._event_handlers["on_audio_data"].handlers[0]

        asyncio.run(handler(buffer, b"\x00\x01", 24000, 1))

        assert s._recorded_audio == (b"\x00\x01", 24000, 1)


class TestSaveSessionAudio:

    def test_should_save_recording_for_the_session_row(self):
        s = _make()
        s._recorded_audio = (b"\x00\x01", 24000, 1)

        s._save_session_audio(ENTRY)

        s._session_audio_recording_service.save_recording.assert_called_once_with(4, b"\x00\x01", 24000, 1)

    def test_should_swallow_and_warn_on_failure(self):
        s = _make()
        s._recorded_audio = (b"\x00\x01", 24000, 1)
        s._session_audio_recording_service.save_recording.side_effect = RuntimeError("disk full")

        s._save_session_audio(ENTRY)  # must not raise

        assert s._logging_broker.log_warning.call_count == 1

    @pytest.mark.parametrize("entry, audio", [(None, (b"x", 1, 1)), (ENTRY, None)])
    def test_should_noop_without_entry_or_audio(self, entry, audio):
        s = _make()
        s._recorded_audio = audio

        s._save_session_audio(entry)

        s._session_audio_recording_service.save_recording.assert_not_called()

    def test_should_noop_when_no_service_wired(self):
        s = _make(with_service=False)
        s._recorded_audio = (b"x", 1, 1)

        s._save_session_audio(ENTRY)  # nothing wired: must simply not raise
