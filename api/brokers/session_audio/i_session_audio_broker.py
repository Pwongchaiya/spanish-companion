"""Broker interface for `session_audio` persistence.

`typing.Protocol`, not `ABC`, per CLAUDE.md's Broker-interfaces waiver. Pure
CRUD plus the two reads E3 needs (by session, older-than for retention).
Mirrors api/brokers/persona/i_persona_broker.py.
"""

from datetime import datetime
from typing import Optional, Protocol

from api.models.foundations.session_audio.session_audio import SessionAudio


class ISessionAudioBroker(Protocol):
    """External-resource boundary for `session_audio` persistence. Raw
    SQLAlchemy only -- no business logic, no exception handling."""

    def insert_session_audio(self, session_audio: SessionAudio) -> SessionAudio:
        """Insert one row from `session_audio` (its `id` is ignored) and return
        it with the assigned id."""
        ...

    def select_session_audio_by_session_log_id(self, session_log_id: int) -> Optional[SessionAudio]:
        """The newest row for this session, or None."""
        ...

    def select_session_audio_older_than(self, cutoff: datetime) -> list[SessionAudio]:
        """Every row with created_at strictly before `cutoff`, id ascending."""
        ...

    def delete_session_audio(self, session_audio_id: int) -> Optional[SessionAudio]:
        """Delete the row and return it as it was. None if it doesn't exist."""
        ...
