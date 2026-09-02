"""Shared fixtures for IngestionService unit tests.

Per CLAUDE.md's Phase 2 test strategy every dependency is mocked. Ingestion now
depends on the two Foundation services rather than the brokers directly, so the
mocks are specced against IChunkRepositoryService / IEmbeddingModelService --
no Postgres, no sentence-transformers model load. Chunk boundaries are derived
from the service's own CHUNK_SIZE rather than hardcoded to 800, so the tests
stay deterministic even if the CHUNK_SIZE env knob is set locally.
"""

from unittest.mock import Mock

import pytest

from rag.services.foundations.chunk_repository import IChunkRepositoryService
from rag.services.foundations.embedding_model import IEmbeddingModelService
from rag.services.orchestrations.ingestion import IngestionService


@pytest.fixture
def mock_chunk_repository():
    return Mock(spec=IChunkRepositoryService)


@pytest.fixture
def mock_embedding_model():
    return Mock(spec=IEmbeddingModelService)


@pytest.fixture
def service(mock_chunk_repository, mock_embedding_model):
    return IngestionService(
        chunk_repository_service=mock_chunk_repository,
        embedding_model_service=mock_embedding_model,
    )
