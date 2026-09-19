"""Unit tests for ProgressOrchestrationService's two session-log
aggregates -- get_speaking_total() (roadmap C1) and
get_longest_unflagged_streak() (roadmap C3).

Both fold the same `session_log` rows, so the rules about which rows count
at all (completed only, no negative durations) are exercised against each.
Every datetime is a fixed literal; no datetime.now() anywhere.
"""

from datetime import datetime, timedelta

import pytest

from tests.unit.services.progress.conftest import FIXED_NOW


@pytest.fixture(autouse=True)
def _no_profile_reads(mock_learner_profile_processing_service):
    """C1/C3 must not resolve a profile -- `session_log` has no profile_id,
    so ensure_profile() would be a pointless write on a read path. Asserted
    after every test in this module."""
    yield
    assert mock_learner_profile_processing_service.ensure_profile.call_count == 0


class TestGetSpeakingTotal:

    def test_should_sum_durations_of_completed_sessions(
        self, service, mock_session_log_entry_service, make_session
    ):
        # given -- 30 + 15 minutes
        mock_session_log_entry_service.list_session_log_entries.return_value = [
            make_session(entry_id=1, minutes=30),
            make_session(entry_id=2, started_at=FIXED_NOW + timedelta(days=1), minutes=15),
        ]

        # when
        actual = service.get_speaking_total()

        # then
        assert actual.total_seconds == 45 * 60
        assert actual.session_count == 2
        mock_session_log_entry_service.list_session_log_entries.assert_called_once_with()

    def test_should_return_zero_when_no_sessions_logged(self, service, mock_session_log_entry_service):
        mock_session_log_entry_service.list_session_log_entries.return_value = []

        actual = service.get_speaking_total()

        assert actual.total_seconds == 0
        assert actual.session_count == 0

    def test_should_skip_in_flight_sessions(self, service, mock_session_log_entry_service, make_session):
        # given -- one completed, one still running (ended_at is None)
        mock_session_log_entry_service.list_session_log_entries.return_value = [
            make_session(entry_id=1, minutes=30),
            make_session(entry_id=2, started_at=FIXED_NOW + timedelta(days=1), minutes=None),
        ]

        actual = service.get_speaking_total()

        assert actual.total_seconds == 30 * 60
        assert actual.session_count == 1, "an unfinished session must not be counted as a session"

    def test_should_skip_rows_whose_end_precedes_their_start(
        self, service, mock_session_log_entry_service, make_session
    ):
        # given -- a clock change mid-session; counting it would subtract
        # real hours from the meter.
        mock_session_log_entry_service.list_session_log_entries.return_value = [
            make_session(entry_id=1, minutes=30),
            make_session(entry_id=2, started_at=FIXED_NOW + timedelta(days=1), minutes=-10),
        ]

        actual = service.get_speaking_total()

        assert actual.total_seconds == 30 * 60
        assert actual.session_count == 1


class TestGetLongestUnflaggedStreak:

    def _sessions(self, make_session, *flag_counts):
        return [
            make_session(entry_id=i + 1, started_at=FIXED_NOW + timedelta(days=i), flag_count=count)
            for i, count in enumerate(flag_counts)
        ]

    def test_should_return_zero_when_no_sessions_logged(self, service, mock_session_log_entry_service):
        mock_session_log_entry_service.list_session_log_entries.return_value = []

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 0
        assert actual.current == 0

    def test_should_count_a_run_of_clean_sessions(
        self, service, mock_session_log_entry_service, make_session
    ):
        # 0, 0, 0 -> three in a row, still running
        mock_session_log_entry_service.list_session_log_entries.return_value = self._sessions(
            make_session, 0, 0, 0
        )

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 3
        assert actual.current == 3

    def test_should_reset_current_but_keep_longest_after_a_flagged_session(
        self, service, mock_session_log_entry_service, make_session
    ):
        # 0, 0, 0, 2, 0 -> best run of 3, currently 1
        mock_session_log_entry_service.list_session_log_entries.return_value = self._sessions(
            make_session, 0, 0, 0, 2, 0
        )

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 3
        assert actual.current == 1

    def test_should_report_zero_current_when_the_last_session_was_flagged(
        self, service, mock_session_log_entry_service, make_session
    ):
        # 0, 0, 1 -> best run of 2, currently 0
        mock_session_log_entry_service.list_session_log_entries.return_value = self._sessions(
            make_session, 0, 0, 1
        )

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 2
        assert actual.current == 0

    def test_should_return_zero_when_every_session_was_flagged(
        self, service, mock_session_log_entry_service, make_session
    ):
        mock_session_log_entry_service.list_session_log_entries.return_value = self._sessions(
            make_session, 1, 3, 2
        )

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 0
        assert actual.current == 0

    def test_should_not_let_an_in_flight_session_extend_a_streak(
        self, service, mock_session_log_entry_service, make_session
    ):
        # The regression this guards: an in-flight row still carries its
        # insert-time flag_count of 0. Counted naively it would read as a
        # fourth clean session and break the streak's meaning.
        mock_session_log_entry_service.list_session_log_entries.return_value = [
            make_session(entry_id=1, started_at=FIXED_NOW, flag_count=0),
            make_session(entry_id=2, started_at=FIXED_NOW + timedelta(days=1), flag_count=0),
            make_session(entry_id=3, started_at=FIXED_NOW + timedelta(days=2), flag_count=4),
            make_session(entry_id=4, started_at=FIXED_NOW + timedelta(days=3), minutes=None, flag_count=0),
        ]

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 2
        assert actual.current == 0, "an unfinished session must not start a streak"

    def test_should_respect_start_order_not_insertion_order(
        self, service, mock_session_log_entry_service, make_session
    ):
        # The broker sorts by started_at; the service must not re-sort or
        # assume id order. Ids here are deliberately reversed against time.
        mock_session_log_entry_service.list_session_log_entries.return_value = [
            make_session(entry_id=9, started_at=datetime(2026, 1, 1), flag_count=0),
            make_session(entry_id=8, started_at=datetime(2026, 1, 2), flag_count=0),
            make_session(entry_id=7, started_at=datetime(2026, 1, 3), flag_count=1),
        ]

        actual = service.get_longest_unflagged_streak()

        assert actual.longest == 2
        assert actual.current == 0


class TestGetLatestCompletedSession:
    """get_latest_completed_session() (roadmap C2) -- the same completed-only,
    started_at-ordered fold as C1/C3, returning the last row instead of an
    aggregate over all of them."""

    def test_should_return_none_when_no_sessions_logged(self, service, mock_session_log_entry_service):
        mock_session_log_entry_service.list_session_log_entries.return_value = []

        assert service.get_latest_completed_session() is None

    def test_should_return_the_most_recently_started_completed_session(
        self, service, mock_session_log_entry_service, make_session
    ):
        first = make_session(entry_id=1, started_at=FIXED_NOW, minutes=30, flag_count=2)
        second = make_session(entry_id=2, started_at=FIXED_NOW + timedelta(days=1), minutes=10, flag_count=0)
        mock_session_log_entry_service.list_session_log_entries.return_value = [first, second]

        actual = service.get_latest_completed_session()

        assert actual is second

    def test_should_skip_a_trailing_in_flight_session(
        self, service, mock_session_log_entry_service, make_session
    ):
        completed = make_session(entry_id=1, started_at=FIXED_NOW, minutes=30, flag_count=1)
        still_running = make_session(entry_id=2, started_at=FIXED_NOW + timedelta(days=1), minutes=None)
        mock_session_log_entry_service.list_session_log_entries.return_value = [completed, still_running]

        actual = service.get_latest_completed_session()

        assert actual is completed, "an unfinished trailing session must not be reported as the latest recap"
