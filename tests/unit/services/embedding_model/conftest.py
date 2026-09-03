"""Shared fixtures for EmbeddingModelService unit tests.

Per CLAUDE.md's Phase 2 test strategy and the Foundation layer's mock
target: EmbeddingModelBroker is mocked via unittest.mock.Mock(spec=...) --
no real sentence-transformers model load. No logging_broker mock, same
choice tests/unit/services/ingestion/conftest.py and
tests/unit/services/chunk_repository/conftest.py made: the service defaults
its own (StdlibLoggingBroker).
"""

from unittest.mock import Mock

import pytest

from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.services.foundations.embedding_model import EmbeddingModelService


@pytest.fixture
def mock_broker():
    return Mock(spec=EmbeddingModelBroker)


@pytest.fixture
def service(mock_broker):
    return EmbeddingModelService(embedding_model=mock_broker)
