"""Shared fixtures for EmbeddingModelService unit tests.

Per CLAUDE.md's Phase 2 test strategy and the Foundation layer's mock
target: EmbeddingModelBroker is mocked via unittest.mock.Mock(spec=...) --
no real sentence-transformers model load. logging_broker is now a required
constructor argument (audit M4), mocked here rather than defaulted.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.brokers.logging import LoggingBroker
from rag.services.foundations.embedding_model import EmbeddingModelService


@pytest.fixture
def mock_broker():
    return Mock(spec=EmbeddingModelBroker)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(mock_broker, mock_logging_broker):
    return EmbeddingModelService(embedding_model=mock_broker, logging_broker=mock_logging_broker)
