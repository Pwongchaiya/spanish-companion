"""Orchestration service for transcript replay (roadmap E3).

Composes three Foundation services -- ISessionAudioService (the recording),
ISessionLogEntryService (session start/end), IFlagService (flags with
timestamps) -- into the replay timeline. Three dependencies keeps the Florance
2-3 rule without a waiver; only logging_broker is held directly.

Flag timeline: offset_seconds = flag.timestamp - session started_at.

Flag source (added 2026-09-24): if a per-session snapshot exists
(FlagService.get_session_flags(), written by Voice Conversation at teardown),
that snapshot IS this session's flags -- used directly, no time-window filter
needed. A session recorded before that feature shipped has no snapshot
(get_session_flags() returns None); those fall back to the original behaviour
unchanged -- filtering list_flags() (flags.json, overwritten every session) by
[started_at, ended_at], which only ever finds flags for the most recent
session.

Status (added 2026-09-24): PATCH /review/flags/<id> writes status into
flags.json only, never into a per-session snapshot. So a snapshot flag's
status may be stale -- current flags.json (list_flags()) is checked for a
same-id row first; its status wins when present, else the snapshot's own
status is used.
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

            session_flags = self._flag_service.get_session_flags(session_log_id)
            if session_flags is not None:
                current_status_by_id = {f.id: f.status for f in self._flag_service.list_flags()}
                source = [(f, current_status_by_id.get(f.id, f.status)) for f in session_flags]
            else:
                source = [
                    (f, f.status)
                    for f in self._flag_service.list_flags()
                    if entry.started_at <= f.timestamp <= window_end
                ]

            flags = []
            for flag, status in source:
                offset = (flag.timestamp - entry.started_at).total_seconds()
                flags.append(
                    ReplayFlag(
                        flag_id=flag.id,
                        offset_seconds=min(offset, audio.duration_seconds),
                        said=flag.said,
                        corrected=flag.corrected,
                        category=flag.category,
                        status=status,
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
