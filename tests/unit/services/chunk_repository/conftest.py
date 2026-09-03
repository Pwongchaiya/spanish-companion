"""Shared fixtures for ChunkRepositoryService unit tests.

Per CLAUDE.md's Phase 2 test strategy and the Foundation layer's mock
target: ChunkRepositoryBroker is mocked via unittest.mock.Mock(spec=...) --
no real Postgres/pgvector. Mirrors tests/unit/services/generation/conftest.py's
shape one broker over, and tests/unit/services/ingestion/conftest.py's choice
not to mock a logging_broker: ChunkRepositoryService defaults its own
(StdlibLoggingBroker), matching Ingestion's identical default-and-don't-assert
posture cited in chunk_repository_service_exceptions.py's own docstring.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository import ChunkRepositoryService


@pytest.fixture
def mock_broker():
    return Mock(spec=ChunkRepositoryBroker)


@pytest.fixture
def service(mock_broker):
    return ChunkRepositoryService(chunk_repository=mock_broker)


@pytest.fixture
def chunk():
    return ScoredChunk(
        chunk_id=1,
        topic="preterite-vs-imperfect",
        source_url="https://www.rae.es/gram/preterito",
        content="El pretérito indefinido expresa acciones acabadas.",
        score=0.12,
    )
