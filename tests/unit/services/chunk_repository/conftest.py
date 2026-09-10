"""Shared fixtures for ChunkRepositoryService unit tests.

Per CLAUDE.md's Phase 2 test strategy and the Foundation layer's mock
target: ChunkRepositoryBroker is mocked via unittest.mock.Mock(spec=...) --
no real Postgres/pgvector. logging_broker is now a required constructor
argument (audit M4), mocked here rather than defaulted.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.chunk_repository import ChunkRepositoryBroker
from rag.brokers.logging import LoggingBroker
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository import ChunkRepositoryService


@pytest.fixture
def mock_broker():
    return Mock(spec=ChunkRepositoryBroker)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service(mock_broker, mock_logging_broker):
    return ChunkRepositoryService(chunk_repository=mock_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def chunk():
    return ScoredChunk(
        chunk_id=1,
        topic="preterite-vs-imperfect",
        source_url="https://www.rae.es/gram/preterito",
        content="El pretérito indefinido expresa acciones acabadas.",
        score=0.12,
    )
