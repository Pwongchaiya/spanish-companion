"""Unit tests for SessionLogEntryService's happy-path flow: each public
method delegates to exactly one broker call and returns its result
unchanged.

Strict call-count verification on every mock touch, per CLAUDE.md's Phase 2
test strategy.
"""

from tests.unit.services.session_log_entry.conftest import FIXED_END, FIXED_START


class TestCreateSessionLogEntry:

    def test_should_insert_in_flight_row_and_return_it(
        self, service, mock_session_log_entry_broker, make_entry
    ):
        # given
        entry = make_entry(entry_id=7)
        mock_session_log_entry_broker.insert_session_log_entry.return_value = entry

        # when
        actual = service.create_session_log_entry(FIXED_START)

        # then
        assert actual is entry
        mock_session_log_entry_broker.insert_session_log_entry.assert_called_once_with(FIXED_START, None)


class TestListSessionLogEntries:

    def test_should_return_broker_rows_unchanged(self, service, mock_session_log_entry_broker, make_entry):
        # given
        entries = [make_entry(entry_id=1), make_entry(entry_id=2)]
        mock_session_log_entry_broker.select_all_session_log_entries.return_value = entries

        # when
        actual = service.list_session_log_entries()

        # then
        assert actual == entries
        mock_session_log_entry_broker.select_all_session_log_entries.assert_called_once_with()

    def test_should_return_empty_list_when_no_sessions_logged(self, service, mock_session_log_entry_broker):
        # given
        mock_session_log_entry_broker.select_all_session_log_entries.return_value = []

        # when / then
        assert service.list_session_log_entries() == []


class TestCompleteSessionLogEntry:

    def test_should_write_ended_at_and_flag_count(self, service, mock_session_log_entry_broker, make_entry):
        # given
        completed = make_entry(entry_id=7, ended_at=FIXED_END, flag_count=3)
        mock_session_log_entry_broker.update_session_log_entry.return_value = completed

        # when
        actual = service.complete_session_log_entry(7, FIXED_END, 3)

        # then
        assert actual is completed
        mock_session_log_entry_broker.update_session_log_entry.assert_called_once_with(7, FIXED_END, 3)

    def test_should_accept_zero_flag_count(self, service, mock_session_log_entry_broker, make_entry):
        # given -- zero is the whole point of C3, so it must not be rejected
        # as falsy anywhere along the path.
        mock_session_log_entry_broker.update_session_log_entry.return_value = make_entry(
            entry_id=7, ended_at=FIXED_END, flag_count=0
        )

        # when
        actual = service.complete_session_log_entry(7, FIXED_END, 0)

        # then
        assert actual.flag_count == 0
        mock_session_log_entry_broker.update_session_log_entry.assert_called_once_with(7, FIXED_END, 0)


class TestCreateWithScenario:

    def test_should_pass_scenario_slug_to_broker(self, service, mock_session_log_entry_broker, make_entry):
        # given
        mock_session_log_entry_broker.insert_session_log_entry.return_value = make_entry(entry_id=7)

        # when
        service.create_session_log_entry(FIXED_START, "ordering_coffee")

        # then
        mock_session_log_entry_broker.insert_session_log_entry.assert_called_once_with(FIXED_START, "ordering_coffee")


class TestSetTaskOutcome:

    def test_should_write_outcome_and_return_row(self, service, mock_session_log_entry_broker, make_entry):
        # given
        updated = make_entry(entry_id=7)
        mock_session_log_entry_broker.update_session_log_entry_task_outcome.return_value = updated

        # when
        actual = service.set_task_outcome(7, "success")

        # then
        assert actual is updated
        mock_session_log_entry_broker.update_session_log_entry_task_outcome.assert_called_once_with(7, "success")
