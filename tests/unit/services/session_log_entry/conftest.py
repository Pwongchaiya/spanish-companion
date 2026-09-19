"""Shared fixtures for SessionLogEntryService unit tests.

Per CLAUDE.md's Phase 2 test strategy: the broker is mocked via
Mock(spec=ISessionLogEntryBroker) at its Protocol boundary, never the real
SqlAlchemy one, which would drag in Postgres. Every datetime is a fixed
literal -- no datetime.now() anywhere in this suite.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.session_log_entry import ISessionLogEntryBroker
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.services.foundations.session_log_entry import SessionLogEntryService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_START = datetime(2026, 1, 2, 10, 0, 0)
FIXED_END = datetime(2026, 1, 2, 10, 42, 0)


@pytest.fixture
def mock_session_log_entry_broker():
    return Mock(spec=ISessionLogEntryBroker)


@pytest.fixture
def service(mock_session_log_entry_broker, mock_logging_broker):
    return SessionLogEntryService(mock_session_log_entry_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def make_entry():
    def _make(
        entry_id: int = 1,
        started_at: datetime = FIXED_START,
        ended_at: datetime | None = None,
        flag_count: int = 0,
    ) -> SessionLogEntry:
        return SessionLogEntry(
            id=entry_id,
            started_at=started_at,
            ended_at=ended_at,
            flag_count=flag_count,
        )

    return _make
