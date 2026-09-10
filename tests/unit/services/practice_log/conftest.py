"""Shared fixtures for PracticeLogService unit tests.

Per CLAUDE.md's Phase 2 test strategy: PracticeLogBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live file I/O. Attempt
timestamps are supplied by the caller (ReviewOrchestrationService's injected clock),
not read live here, so no fake clock is needed at this layer.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.logging import LoggingBroker
from api.brokers.practice_log import PracticeAttempt, PracticeLogBroker
from api.services.foundations.practice_log import PracticeLogService

FIXED_TIMESTAMP = datetime(2026, 1, 2, 3, 4, 5)


@pytest.fixture
def mock_practice_log_broker():
    return Mock(spec=PracticeLogBroker)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(mock_practice_log_broker, mock_logging_broker):
    return PracticeLogService(practice_log_broker=mock_practice_log_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def make_attempt():
    def _make(flag_id: str = "flag-1", attempt_text: str = "fui al mercado") -> PracticeAttempt:
        return PracticeAttempt(flag_id=flag_id, attempt_text=attempt_text, timestamp=FIXED_TIMESTAMP)

    return _make
