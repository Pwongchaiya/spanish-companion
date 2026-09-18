"""Shared fixtures for TtsService unit tests.

Per CLAUDE.md's Phase 2 test strategy: TtsBroker is mocked via
unittest.mock.Mock(spec=TtsBroker) -- no live Azure Speech SDK call.
"""

from unittest.mock import Mock

import pytest

from api.brokers.tts import TtsBroker
from api.services.foundations.tts import TtsService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401


@pytest.fixture
def mock_broker():
    return Mock(spec=TtsBroker)


@pytest.fixture
def service(mock_broker, mock_logging_broker):
    return TtsService(mock_broker, logging_broker=mock_logging_broker)
