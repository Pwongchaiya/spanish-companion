"""Shared fixtures for LiveTranscriptService unit tests.

Per CLAUDE.md's Phase 2 test strategy: SessionLogBroker is mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no live file I/O.
"""

from unittest.mock import Mock

import pytest

from api.brokers.session_log import SessionLogBroker
from api.services.foundations.live_transcript import LiveTranscriptService


@pytest.fixture
def mock_session_log_broker():
    return Mock(spec=SessionLogBroker)


@pytest.fixture
def service(mock_session_log_broker):
    return LiveTranscriptService(session_log_broker=mock_session_log_broker)
