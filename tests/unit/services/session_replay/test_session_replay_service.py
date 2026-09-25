"""SessionReplayOrchestrationService: timeline math, window filtering, tiers.
All datetimes are fixed literals."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.logging import LoggingBroker
from api.models.foundations.flag import Flag
from api.models.foundations.flag.exceptions import FlagDependencyException
from api.models.foundations.session_audio.exceptions import (
    NotFoundSessionAudioException,
    SessionAudioDependencyException,
    SessionAudioValidationException,
)
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.models.orchestrations.session_replay.exceptions import (
    NotFoundSessionReplayException,
    SessionReplayOrchestrationDependencyException,
    SessionReplayOrchestrationServiceException,
    SessionReplayOrchestrationValidationException,
)
from api.services.foundations.flag import IFlagService
from api.services.foundations.session_audio import ISessionAudioService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.orchestrations.session_replay import SessionReplayOrchestrationService

START = datetime(2026, 3, 1, 10, 0, 0)
END = datetime(2026, 3, 1, 10, 5, 0)


def _flag(flag_id: str, at: datetime) -> Flag:
    return Flag(id=flag_id, said="yo tiene", corrected="yo tengo", category="conjugation", timestamp=at)


@pytest.fixture
def audio_service():
    return Mock(spec=ISessionAudioService)


@pytest.fixture
def flag_service():
    mock = Mock(spec=IFlagService)
    # Default: no per-session snapshot -- every existing test below exercises
    # the pre-E3 time-window fallback unchanged. Tests for the snapshot path
    # override this explicitly.
    mock.get_session_flags.return_value = None
    return mock


@pytest.fixture
def entry_service():
    return Mock(spec=ISessionLogEntryService)


@pytest.fixture
def logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(audio_service, flag_service, entry_service, logging_broker):
    return SessionReplayOrchestrationService(
        audio_service, flag_service, entry_service, logging_broker=logging_broker
    )


@pytest.fixture
def wired(audio_service, entry_service):
    audio_service.get_session_audio_by_session_log_id.return_value = SessionAudio(
        1, 4, "data/audio/session_4.wav", 300.0, END
    )
    entry_service.list_session_log_entries.return_value = [
        SessionLogEntry(3, datetime(2026, 2, 1), datetime(2026, 2, 1, 0, 5), 0),
        SessionLogEntry(4, START, END, 3),
    ]


def test_get_replay_should_compute_offsets_and_exclude_flags_outside_the_session(
    service, wired, flag_service, audio_service, entry_service
):
    flag_service.list_flags.return_value = [
        _flag("late", datetime(2026, 3, 1, 10, 2, 30)),
        _flag("early", datetime(2026, 3, 1, 10, 0, 12, 500000)),
        _flag("older-session", datetime(2026, 2, 28, 9, 0, 0)),
        _flag("after", datetime(2026, 3, 1, 11, 0, 0)),
    ]

    replay = service.get_replay(4)

    assert replay.session_log_id == 4 and replay.duration_seconds == 300.0
    assert [(f.flag_id, f.offset_seconds) for f in replay.flags] == [("early", 12.5), ("late", 150.0)]
    assert (replay.flags[0].said, replay.flags[0].corrected, replay.flags[0].category) == (
        "yo tiene",
        "yo tengo",
        "conjugation",
    )
    audio_service.get_session_audio_by_session_log_id.assert_called_once_with(4)
    assert entry_service.list_session_log_entries.call_count == 1
    assert flag_service.list_flags.call_count == 1


def test_get_replay_should_use_audio_duration_as_window_end_when_session_never_ended(
    service, audio_service, entry_service, flag_service
):
    audio_service.get_session_audio_by_session_log_id.return_value = SessionAudio(1, 4, "p.wav", 60.0, END)
    entry_service.list_session_log_entries.return_value = [SessionLogEntry(4, START, None, 0)]
    flag_service.list_flags.return_value = [
        _flag("in", datetime(2026, 3, 1, 10, 0, 30)),
        _flag("out", datetime(2026, 3, 1, 10, 3, 0)),
    ]

    assert [f.flag_id for f in service.get_replay(4).flags] == ["in"]


def test_get_replay_should_use_the_session_snapshot_when_one_exists(service, wired, flag_service, audio_service):
    # A flag well outside [started_at, ended_at] -- the fallback filter would
    # drop it, but a snapshot IS this session's flags, so no window filter
    # applies.
    flag_service.get_session_flags.return_value = [_flag("snap", datetime(2026, 3, 1, 11, 0, 0))]
    flag_service.list_flags.return_value = []

    replay = service.get_replay(4)

    assert [f.flag_id for f in replay.flags] == ["snap"]
    flag_service.get_session_flags.assert_called_once_with(4)


def test_get_replay_should_prefer_flags_json_status_over_the_snapshots_when_the_id_still_exists(
    service, wired, flag_service
):
    snapshot_flag = _flag("f1", datetime(2026, 3, 1, 10, 1, 0))
    snapshot_flag.status = "mastered"  # stale -- PATCH only ever writes flags.json
    flag_service.get_session_flags.return_value = [snapshot_flag]
    current_flag = _flag("f1", datetime(2026, 3, 1, 10, 1, 0))
    current_flag.status = "skipped"  # current flags.json value should win
    flag_service.list_flags.return_value = [current_flag]

    replay = service.get_replay(4)

    assert replay.flags[0].status == "skipped"


def test_get_replay_should_use_the_snapshots_own_status_when_the_id_is_gone_from_flags_json(
    service, wired, flag_service
):
    snapshot_flag = _flag("f1", datetime(2026, 3, 1, 10, 1, 0))
    snapshot_flag.status = "mastered"
    flag_service.get_session_flags.return_value = [snapshot_flag]
    flag_service.list_flags.return_value = []  # a later session's save_flags() overwrote it away

    replay = service.get_replay(4)

    assert replay.flags[0].status == "mastered"


def test_get_replay_should_default_status_to_open_in_the_fallback_path(service, wired, flag_service):
    flag_service.list_flags.return_value = [_flag("f1", datetime(2026, 3, 1, 10, 1, 0))]

    replay = service.get_replay(4)

    assert replay.flags[0].status == "open"


def test_get_replay_should_raise_validation_when_audio_missing(service, audio_service, flag_service, entry_service):
    audio_service.get_session_audio_by_session_log_id.side_effect = SessionAudioValidationException(
        inner_exception=NotFoundSessionAudioException()
    )

    with pytest.raises(SessionReplayOrchestrationValidationException) as caught:
        service.get_replay(4)

    assert isinstance(caught.value.inner_exception.inner_exception, NotFoundSessionAudioException)
    assert flag_service.list_flags.call_count == 0 and entry_service.list_session_log_entries.call_count == 0


def test_get_replay_should_raise_validation_when_session_row_missing(service, wired, entry_service, flag_service):
    entry_service.list_session_log_entries.return_value = []

    with pytest.raises(SessionReplayOrchestrationValidationException) as caught:
        service.get_replay(4)

    assert isinstance(caught.value.inner_exception, NotFoundSessionReplayException)
    assert flag_service.list_flags.call_count == 0


@pytest.mark.parametrize("failing", ["audio", "flag"])
def test_get_replay_should_wrap_dependency_failures(
    service, wired, audio_service, flag_service, logging_broker, failing
):
    flag_service.list_flags.return_value = []
    if failing == "audio":
        audio_service.get_session_audio_by_session_log_id.side_effect = SessionAudioDependencyException(
            inner_exception=OSError("db down")
        )
    else:
        flag_service.list_flags.side_effect = FlagDependencyException(inner_exception=OSError("disk"))

    with pytest.raises(SessionReplayOrchestrationDependencyException):
        service.get_replay(4)

    assert logging_broker.log_error.call_count == 1


def test_get_replay_should_wrap_unexpected_error_as_service_exception(service, wired, flag_service):
    flag_service.list_flags.side_effect = RuntimeError("boom")

    with pytest.raises(SessionReplayOrchestrationServiceException):
        service.get_replay(4)


def test_get_audio_should_return_row_without_touching_flags(service, audio_service, flag_service, entry_service):
    row = SessionAudio(1, 4, "p.wav", 60.0, END)
    audio_service.get_session_audio_by_session_log_id.return_value = row

    assert service.get_audio(4) is row
    assert flag_service.list_flags.call_count == 0 and entry_service.list_session_log_entries.call_count == 0


def test_get_latest_session_id_should_return_the_newest_recordings_session(service, audio_service):
    audio_service.get_latest_session_audio.return_value = SessionAudio(9, 6, "p.wav", 60.0, END)

    assert service.get_latest_session_id() == 6
    assert audio_service.get_latest_session_audio.call_count == 1


def test_get_latest_session_id_should_raise_validation_when_nothing_recorded(service, audio_service):
    audio_service.get_latest_session_audio.side_effect = SessionAudioValidationException(
        inner_exception=NotFoundSessionAudioException()
    )

    with pytest.raises(SessionReplayOrchestrationValidationException):
        service.get_latest_session_id()
