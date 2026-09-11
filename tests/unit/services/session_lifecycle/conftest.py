"""Shared fixtures for ConversationSessionService unit tests.

Per CLAUDE.md's Phase 2 test strategy: BotProcessBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live time.sleep()/datetime.now()
reads, so time is injected as a fake, test-controlled clock instead.

ConfigurationBroker is likewise faked (FakeConfigurationBroker) rather than
reading real env vars -- this is the exact testability seam the H1 audit
finding (no import-time env read) exists to create. GRACEFUL_TIMEOUT_SECONDS
/ TERMINATE_TIMEOUT_SECONDS / READY_WARMUP_SECONDS constants are gone from
the module (they were the import-time read); tests get the same fixed,
known values by asserting against this fake's `values` dict instead.
"""

import pytest
from unittest.mock import Mock

from api.brokers.bot_process import BotProcessBroker
from api.brokers.configuration import ConfigurationBroker
from api.services.foundations.session_lifecycle import ConversationSessionService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

GRACEFUL_TIMEOUT_SECONDS = 5.0
TERMINATE_TIMEOUT_SECONDS = 2.0
READY_WARMUP_SECONDS = 16.0


class FakeClock:
    """Deterministic, manually-advanced stand-in for time.monotonic."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class FakeConfigurationBroker:
    """Dict-backed ConfigurationBroker stub -- fixed, known config values."""

    def __init__(self, values: dict) -> None:
        self._values = values

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._values.get(key, default)

    def require(self, key: str) -> str:
        return self._values[key]


@pytest.fixture
def mock_broker():
    return Mock(spec=BotProcessBroker)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def configuration_broker() -> ConfigurationBroker:
    return FakeConfigurationBroker(
        {
            "SESSION_GRACEFUL_TIMEOUT_SECONDS": str(GRACEFUL_TIMEOUT_SECONDS),
            "SESSION_TERMINATE_TIMEOUT_SECONDS": str(TERMINATE_TIMEOUT_SECONDS),
            "SESSION_READY_WARMUP_SECONDS": str(READY_WARMUP_SECONDS),
        }
    )


@pytest.fixture
def service(mock_broker, clock, mock_logging_broker, configuration_broker):
    return ConversationSessionService(
        broker=mock_broker,
        time_source=clock,
        logging_broker=mock_logging_broker,
        configuration_broker=configuration_broker,
    )
