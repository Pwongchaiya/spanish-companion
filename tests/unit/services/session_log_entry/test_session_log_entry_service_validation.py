"""Unit tests for SessionLogEntryService's input validation.

Every rejection must happen before the broker is touched -- asserted
explicitly on call_count, per CLAUDE.md's Phase 2 test strategy.
"""

import pytest

from api.models.foundations.session_log_entry.exceptions import (
    InvalidSessionLogEntryException,
    SessionLogEntryValidationException,
)
from tests.unit.services.session_log_entry.conftest import FIXED_END, FIXED_START


class TestCreateValidation:

    @pytest.mark.parametrize("bad_started_at", [None, "2026-01-02", 1767348000, object()])
    def test_should_reject_non_datetime_started_at(
        self, service, mock_session_log_entry_broker, bad_started_at
    ):
        with pytest.raises(SessionLogEntryValidationException) as caught:
            service.create_session_log_entry(bad_started_at)

        assert isinstance(caught.value.inner_exception, InvalidSessionLogEntryException)
        assert "started_at" in caught.value.inner_exception.errors
        assert mock_session_log_entry_broker.insert_session_log_entry.call_count == 0


class TestCompleteValidation:

    @pytest.mark.parametrize("bad_entry_id", [None, 0, -1, True, "1"])
    def test_should_reject_non_positive_entry_id(self, service, mock_session_log_entry_broker, bad_entry_id):
        with pytest.raises(SessionLogEntryValidationException) as caught:
            service.complete_session_log_entry(bad_entry_id, FIXED_END, 0)

        assert "entry_id" in caught.value.inner_exception.errors
        assert mock_session_log_entry_broker.update_session_log_entry.call_count == 0

    @pytest.mark.parametrize("bad_ended_at", [None, "2026-01-02", 0])
    def test_should_reject_non_datetime_ended_at(self, service, mock_session_log_entry_broker, bad_ended_at):
        with pytest.raises(SessionLogEntryValidationException) as caught:
            service.complete_session_log_entry(1, bad_ended_at, 0)

        assert "ended_at" in caught.value.inner_exception.errors
        assert mock_session_log_entry_broker.update_session_log_entry.call_count == 0

    @pytest.mark.parametrize("bad_flag_count", [None, -1, "3", 2.5, True])
    def test_should_reject_invalid_flag_count(self, service, mock_session_log_entry_broker, bad_flag_count):
        with pytest.raises(SessionLogEntryValidationException) as caught:
            service.complete_session_log_entry(1, FIXED_END, bad_flag_count)

        assert "flag_count" in caught.value.inner_exception.errors
        assert mock_session_log_entry_broker.update_session_log_entry.call_count == 0

    def test_should_report_every_failing_field_at_once(self, service, mock_session_log_entry_broker):
        # Batched reporting, not fail-fast -- mirrors NL.Core.Users' Xeption
        # UpsertDataList/ThrowIfContainsErrors contract.
        with pytest.raises(SessionLogEntryValidationException) as caught:
            service.complete_session_log_entry(0, None, -1)

        assert set(caught.value.inner_exception.errors) == {"entry_id", "ended_at", "flag_count"}
        assert mock_session_log_entry_broker.update_session_log_entry.call_count == 0

    def test_should_accept_valid_input(self, service, mock_session_log_entry_broker, make_entry):
        mock_session_log_entry_broker.update_session_log_entry.return_value = make_entry(
            started_at=FIXED_START, ended_at=FIXED_END
        )

        service.complete_session_log_entry(1, FIXED_END, 0)

        assert mock_session_log_entry_broker.update_session_log_entry.call_count == 1
