"""Shared fixtures for FlagService unit tests.

Per CLAUDE.md's Phase 2 test strategy: FlagBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live file I/O.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.flag import FlagBroker
from api.brokers.logging import LoggingBroker
from api.models.flag import Flag
from api.services.foundations.flag import FlagService


@pytest.fixture
def mock_flag_broker():
    return Mock(spec=FlagBroker)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(mock_flag_broker, mock_logging_broker):
    return FlagService(flag_broker=mock_flag_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def make_flag():
    def _make(flag_id: str = "flag-1", corrected: str = "fui al mercado", category: str = "preterite") -> Flag:
        return Flag(
            id=flag_id,
            said="iba al mercado ayer",
            corrected=corrected,
            category=category,
            timestamp=datetime(2026, 1, 2, 3, 4, 5),
        )

    return _make
