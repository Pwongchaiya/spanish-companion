"""Shared `mock_logging_broker` fixture for rag/ feature conftest.py files.

Not a conftest.py itself -- pytest only auto-loads fixtures from files named
conftest.py, so each feature's conftest.py imports this fixture by name.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.logging import LoggingBroker


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)
