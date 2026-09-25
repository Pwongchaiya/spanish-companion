"""Unit tests for SessionLogEntryService's exception dispatch: which raw
failure maps to which wrapper tier, and that every wrap is logged exactly
once.

There is deliberately no DependencyValidation tier here -- `session_log`
has no unique constraint, so IntegrityError is a plain storage failure
rather than a recoverable "already exists". That is asserted below so the
absence stays intentional.
"""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from api.models.foundations.session_log_entry.exceptions import (
    FailedSessionLogEntryStorageException,
    NotFoundSessionLogEntryException,
    SessionLogEntryDependencyException,
    SessionLogEntryServiceException,
    SessionLogEntryValidationException,
)
from tests.unit.services.session_log_entry.conftest import FIXED_END, FIXED_START


class TestDependencyTier:

    def test_should_wrap_operational_error_on_create(self, service, mock_session_log_entry_broker, mock_logging_broker):
        mock_session_log_entry_broker.insert_session_log_entry.side_effect = OperationalError(
            "INSERT", {}, Exception("connection refused")
        )

        with pytest.raises(SessionLogEntryDependencyException) as caught:
            service.create_session_log_entry(FIXED_START)

        assert isinstance(caught.value.inner_exception, FailedSessionLogEntryStorageException)
        assert mock_logging_broker.log_error.call_count == 1

    def test_should_wrap_operational_error_on_list(self, service, mock_session_log_entry_broker):
        mock_session_log_entry_broker.select_all_session_log_entries.side_effect = OperationalError(
            "SELECT", {}, Exception("connection refused")
        )

        with pytest.raises(SessionLogEntryDependencyException):
            service.list_session_log_entries()

    def test_should_wrap_integrity_error_as_dependency_not_dependency_validation(
        self, service, mock_session_log_entry_broker
    ):
        mock_session_log_entry_broker.update_session_log_entry.side_effect = IntegrityError(
            "UPDATE", {}, Exception("null value in column violates not-null constraint")
        )

        with pytest.raises(SessionLogEntryDependencyException) as caught:
            service.complete_session_log_entry(1, FIXED_END, 0)

        assert isinstance(caught.value.inner_exception, FailedSessionLogEntryStorageException)


class TestValidationTier:

    def test_should_raise_not_found_when_broker_returns_none(
        self, service, mock_session_log_entry_broker, mock_logging_broker
    ):
        # The broker's None-on-missing-id contract, mapped to a domain
        # exception by the service (never leaked as a None return).
        mock_session_log_entry_broker.update_session_log_entry.return_value = None

        with pytest.raises(SessionLogEntryValidationException) as caught:
            service.complete_session_log_entry(999, FIXED_END, 0)

        assert isinstance(caught.value.inner_exception, NotFoundSessionLogEntryException)
        assert mock_logging_broker.log_error.call_count == 1


class TestServiceTier:

    def test_should_wrap_unexpected_error_as_service_exception(
        self, service, mock_session_log_entry_broker, mock_logging_broker
    ):
        mock_session_log_entry_broker.select_all_session_log_entries.side_effect = ValueError("boom")

        with pytest.raises(SessionLogEntryServiceException) as caught:
            service.list_session_log_entries()

        assert isinstance(caught.value.inner_exception, ValueError)
        assert mock_logging_broker.log_error.call_count == 1
