"""Shared fixtures for SessionLogService unit tests.

Per CLAUDE.md's Phase 2 test strategy: SessionLogBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live file I/O.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.session_log import SessionLogBroker
from api.models.flag import Flag
from api.services.foundations.session_log import SessionLogService


@pytest.fixture
def mock_session_log_broker():
    return Mock(spec=SessionLogBroker)


@pytest.fixture
def service(mock_session_log_broker):
    return SessionLogService(session_log_broker=mock_session_log_broker)


@pytest.fixture
def make_flag():
    def _make(category: str = "preterite") -> Flag:
        return Flag(
            id="flag-1",
            said="iba al mercado ayer",
            corrected="fui al mercado ayer",
            category=category,
            timestamp=datetime(2026, 1, 2, 3, 4, 5),
        )

    return _make
