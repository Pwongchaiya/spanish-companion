"""Shared fixtures for IngestionService unit tests.

Per CLAUDE.md's Phase 2 test strategy: both brokers are mocked via
unittest.mock.Mock(spec=BrokerProtocol) -- no Postgres, no sentence-transformers
model load. Chunk boundaries are derived from the service's own CHUNK_SIZE
rather than hardcoded to 800, so the tests stay deterministic even if the
CHUNK_SIZE env knob is set locally.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.services.ingestion import IngestionService


@pytest.fixture
def mock_chunk_repository():
    return Mock(spec=ChunkRepositoryBroker)


@pytest.fixture
def mock_embedding_model():
    return Mock(spec=EmbeddingModelBroker)


@pytest.fixture
def service(mock_chunk_repository, mock_embedding_model):
    return IngestionService(chunk_repository=mock_chunk_repository, embedding_model=mock_embedding_model)
