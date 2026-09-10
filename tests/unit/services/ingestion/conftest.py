"""Shared fixtures for IngestionService unit tests.

Per CLAUDE.md's Phase 2 test strategy every dependency is mocked. Ingestion now
depends on the two Foundation services rather than the brokers directly, so the
mocks are specced against IChunkRepositoryService / IEmbeddingModelService --
no Postgres, no sentence-transformers model load. Chunk boundaries are derived
from CHUNK_SIZE below, a fixed value handed to the service through a stubbed
ConfigurationBroker (H1's testability seam) rather than read from the real
environment -- the tests stay deterministic no matter what the CHUNK_SIZE env
knob is set to locally.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.configuration import ConfigurationBroker
from rag.brokers.logging import LoggingBroker
from rag.services.foundations.chunk_repository import IChunkRepositoryService
from rag.services.foundations.embedding_model import IEmbeddingModelService
from rag.services.orchestrations.ingestion import IngestionService

CHUNK_SIZE = 800


@pytest.fixture
def mock_chunk_repository():
    return Mock(spec=IChunkRepositoryService)


@pytest.fixture
def mock_embedding_model():
    return Mock(spec=IEmbeddingModelService)


@pytest.fixture
def mock_configuration_broker():
    broker = Mock(spec=ConfigurationBroker)
    broker.get.return_value = str(CHUNK_SIZE)
    return broker


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(mock_chunk_repository, mock_embedding_model, mock_configuration_broker, mock_logging_broker):
    return IngestionService(
        chunk_repository_service=mock_chunk_repository,
        embedding_model_service=mock_embedding_model,
        configuration_broker=mock_configuration_broker,
        logging_broker=mock_logging_broker,
    )
