"""Interface for the session_audio Foundation service (roadmap E3).

typing.Protocol, not abc.ABC, per this project's interface waiver (CLAUDE.md).
Mirrors api/services/foundations/persona/i_persona_service.py.

Every method raises SessionAudioValidationException (wrapping
InvalidSessionAudioException on bad input, or NotFoundSessionAudioException
where noted), SessionAudioDependencyException (wrapping
FailedSessionAudioStorageException) if the broker call fails, and
SessionAudioServiceException for any other unexpected failure.
"""

from datetime import datetime
from typing import Protocol

from api.models.foundations.session_audio.session_audio import SessionAudio


class ISessionAudioService(Protocol):
    """External-facing contract for session_audio's Foundation service."""

    def create_session_audio(self, session_audio: SessionAudio) -> SessionAudio:
        """Insert a row (its `id` is ignored)."""
        ...

    def get_session_audio_by_session_log_id(self, session_log_id: int) -> SessionAudio:
        """The newest audio row for this session. NotFound if none."""
        ...

    def get_latest_session_audio(self) -> SessionAudio:
        """The most recently recorded audio row across all sessions. NotFound if none."""
        ...

    def list_session_audio_older_than(self, cutoff: datetime) -> list[SessionAudio]:
        """Rows created strictly before `cutoff`. Empty list if none."""
        ...

    def delete_session_audio(self, session_audio_id: int) -> SessionAudio:
        """Delete the row and return it. NotFound if missing."""
        ...
