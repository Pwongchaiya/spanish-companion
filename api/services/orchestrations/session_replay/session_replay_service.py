"""Orchestration service for transcript replay (roadmap E3).

Composes three Foundation services -- ISessionAudioService (the recording),
ISessionLogEntryService (session start/end), IFlagService (flags with
timestamps) -- into the replay timeline. Three dependencies keeps the Florance
2-3 rule without a waiver; only logging_broker is held directly.

Flag timeline: offset_seconds = flag.timestamp - session started_at. Flags are
selected by time window [started_at, ended_at] because flags.json holds only
the most recent session's flags (it is overwritten every session, see
FlagService); an older session therefore replays with no flags, never with
another session's flags.
"""

from datetime import timedelta
from typing import Optional

from api.brokers.logging import LoggingBroker
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.models.orchestrations.session_replay.exceptions import NotFoundSessionReplayException
from api.models.orchestrations.session_replay.session_replay import ReplayFlag, SessionReplay
from api.services.foundations.flag import IFlagService
from api.services.foundations.session_audio import ISessionAudioService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.orchestrations.session_replay.i_session_replay_service import ISessionReplayService
from api.services.orchestrations.session_replay.session_replay_service_exceptions import (
    SessionReplayOrchestrationServiceExceptions,
)


class SessionReplayOrchestrationService(SessionReplayOrchestrationServiceExceptions, ISessionReplayService):
    """Owns replay timeline assembly."""

    def __init__(
        self,
        session_audio_service: ISessionAudioService,
        flag_service: IFlagService,
        session_log_entry_service: ISessionLogEntryService,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._session_audio_service = session_audio_service
        self._flag_service = flag_service
        self._session_log_entry_service = session_log_entry_service
        self._logging_broker = logging_broker

    def get_replay(self, session_log_id: int) -> SessionReplay:
        def action() -> SessionReplay:
            audio = self._session_audio_service.get_session_audio_by_session_log_id(session_log_id)
            entry = self._find_entry(session_log_id)
            if entry is None:
                raise NotFoundSessionReplayException()
            window_end = entry.ended_at or entry.started_at + timedelta(seconds=audio.duration_seconds)
            flags = []
            for flag in self._flag_service.list_flags():
                if not entry.started_at <= flag.timestamp <= window_end:
                    continue
                offset = (flag.timestamp - entry.started_at).total_seconds()
                flags.append(
                    ReplayFlag(
                        flag_id=flag.id,
                        offset_seconds=min(offset, audio.duration_seconds),
                        said=flag.said,
                        corrected=flag.corrected,
                        category=flag.category,
                    )
                )
            flags.sort(key=lambda f: f.offset_seconds)
            return SessionReplay(session_log_id=session_log_id, duration_seconds=audio.duration_seconds, flags=flags)

        return self._try_catch(action)

    def get_latest_session_id(self) -> int:
        def action() -> int:
            return self._session_audio_service.get_latest_session_audio().session_log_id

        return self._try_catch(action)

    def get_audio(self, session_log_id: int) -> SessionAudio:
        def action() -> SessionAudio:
            return self._session_audio_service.get_session_audio_by_session_log_id(session_log_id)

        return self._try_catch(action)

    def _find_entry(self, session_log_id: int) -> Optional[SessionLogEntry]:
        # ponytail: linear scan of list_session_log_entries() -- the service has
        # no get-by-id and this is a single-user table. Add one if it ever grows.
        return next(
            (e for e in self._session_log_entry_service.list_session_log_entries() if e.id == session_log_id), None
        )
