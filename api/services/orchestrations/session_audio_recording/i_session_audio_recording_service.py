"""Interface for the Session Audio Recording orchestration service (roadmap E3).

typing.Protocol per this project's interface waiver. Raises
SessionAudioRecordingOrchestrationValidationException /
...DependencyException / ...ServiceException.
"""

from typing import Protocol

from api.models.foundations.session_audio.session_audio import SessionAudio


class ISessionAudioRecordingService(Protocol):
    """External-facing contract: write a session's WAV and its row; prune old ones."""

    def save_recording(self, session_log_id: int, pcm: bytes, sample_rate: int, num_channels: int) -> SessionAudio:
        """Write 16-bit PCM to the audio store and insert its session_audio
        row. If the row insert fails the just-written file is removed again."""
        ...

    def prune_expired(self, retention_days: int) -> int:
        """Delete file + row for every recording older than `retention_days`.
        Returns how many were removed. One bad row never stops the rest."""
        ...
