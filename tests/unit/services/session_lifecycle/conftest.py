"""Shared fixtures for ConversationSessionService unit tests.

Per CLAUDE.md's Phase 2 test strategy: BotProcessBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live time.sleep()/datetime.now()
reads, so time is injected as a fake, test-controlled clock instead.
"""

import pytest
from unittest.mock import Mock

from api.brokers.bot_process import BotProcessBroker
from api.brokers.logging import LoggingBroker
from api.services.foundations.session_lifecycle import ConversationSessionService


class FakeClock:
    """Deterministic, manually-advanced stand-in for time.monotonic."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


@pytest.fixture
def mock_broker():
    return Mock(spec=BotProcessBroker)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(mock_broker, clock, mock_logging_broker):
    return ConversationSessionService(broker=mock_broker, time_source=clock, logging_broker=mock_logging_broker)
