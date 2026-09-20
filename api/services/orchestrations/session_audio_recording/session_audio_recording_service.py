"""Orchestration service for session-audio recording and retention (roadmap E3).

Composes two Foundation services -- IAudioStorageService (the WAV on disk) and
ISessionAudioService (its row). File and row must stay in step, which is the
coordination this tier exists for. Clock injected: CLAUDE.md forbids live
datetime.now() in unit-tested code.
"""

from datetime import datetime, timedelta
from typing import Callable

from api.brokers.logging import LoggingBroker
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.services.foundations.audio_storage import IAudioStorageService
from api.services.foundations.session_audio import ISessionAudioService
from api.services.orchestrations.session_audio_recording.i_session_audio_recording_service import (
    ISessionAudioRecordingService,
)
from api.services.orchestrations.session_audio_recording.session_audio_recording_service_exceptions import (
    SessionAudioRecordingOrchestrationServiceExceptions,
)

_BYTES_PER_SAMPLE = 2  # 16-bit PCM, what Pipecat's audio buffer emits


class SessionAudioRecordingOrchestrationService(
    SessionAudioRecordingOrchestrationServiceExceptions, ISessionAudioRecordingService
):
    """Owns file+row lifecycle for session audio."""

    def __init__(
        self,
        audio_storage_service: IAudioStorageService,
        session_audio_service: ISessionAudioService,
        clock: Callable[[], datetime] = datetime.now,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._audio_storage_service = audio_storage_service
        self._session_audio_service = session_audio_service
        self._clock = clock
        self._logging_broker = logging_broker

    def save_recording(self, session_log_id: int, pcm: bytes, sample_rate: int, num_channels: int) -> SessionAudio:
        def action() -> SessionAudio:
            path = self._audio_storage_service.store_wav(
                f"session_{session_log_id}.wav", pcm, sample_rate, num_channels
            )
            duration = len(pcm) / (sample_rate * num_channels * _BYTES_PER_SAMPLE)
            try:
                return self._session_audio_service.create_session_audio(
                    SessionAudio(
                        id=None,
                        session_log_id=session_log_id,
                        file_path=path,
                        duration_seconds=duration,
                        created_at=self._clock(),
                    )
                )
            except Exception:
                self._audio_storage_service.remove_file(path)  # no orphan file without a row
                raise

        return self._try_catch(action)

    def prune_expired(self, retention_days: int) -> int:
        def action() -> int:
            cutoff = self._clock() - timedelta(days=retention_days)
            removed = 0
            for row in self._session_audio_service.list_session_audio_older_than(cutoff):
                # ponytail: per-row catch so one locked file can't stop the sweep;
                # file goes first, so a failed row delete is retried next startup.
                try:
                    self._audio_storage_service.remove_file(row.file_path)
                    self._session_audio_service.delete_session_audio(row.id)
                    removed += 1
                except Exception as e:  # noqa: BLE001
                    self._logging_broker.log_warning("Session audio prune failed for row %s: %s", row.id, e)
            return removed

        return self._try_catch(action)
