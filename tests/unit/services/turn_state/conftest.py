"""Shared fixtures for TurnStateService unit tests.

Per CLAUDE.md's Phase 2 test strategy: SessionLogBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live file I/O.
"""

from unittest.mock import Mock

import pytest

from api.brokers.session_log import SessionLogBroker
from api.services.foundations.turn_state import TurnStateService


@pytest.fixture
def mock_session_log_broker():
    return Mock(spec=SessionLogBroker)


@pytest.fixture
def service(mock_session_log_broker):
    return TurnStateService(session_log_broker=mock_session_log_broker)
