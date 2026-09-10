"""Shared fixtures for HybridRetrievalService unit tests.

Per CLAUDE.md's Phase 2 test strategy: every dependency is mocked via
unittest.mock.Mock(spec=Protocol), with strict call-count verification on
every mock touched, and deterministic data only. This service's dependencies
are the two Foundation services (IEmbeddingModelService,
IChunkRepositoryService), not raw brokers -- the brokers now sit one layer
further down, behind those services.

Seam note: the service never calls IChunkRepositoryService itself -- it only
passes it to the default DenseVectorStrategy it builds when `strategies` is
not overridden (see HybridRetrievalService.__init__). These tests override
`strategies`, so the repository service is a mock that must stay untouched;
that is asserted in test_retrieve_logic.py rather than assumed. The real
repository path is covered by the Integration tier instead.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.logging import LoggingBroker
from rag.models.retrieval import ScoredChunk
from rag.services.foundations.chunk_repository import IChunkRepositoryService
from rag.services.foundations.embedding_model import IEmbeddingModelService
from rag.services.orchestrations.retrieval import HybridRetrievalService
from rag.services.orchestrations.retrieval.strategies.dense import RetrievalStrategy
from rag.services.orchestrations.retrieval.strategies.fusion import PassThroughRankFusion

# Deterministic stand-in for a 384-dim embedding. Nothing under test does
# vector math -- the dense search that would is the broker's job, exercised
# for real in the Integration tier -- so the only property that matters here
# is that this exact object arrives at every strategy.
QUERY_EMBEDDING = [0.1, 0.2, 0.3]


def chunk(chunk_id: int, topic: str = "preterite-vs-imperfect", score: float = 0.1) -> ScoredChunk:
    """A ScoredChunk with only the fields these tests assert on varied."""
    return ScoredChunk(
        chunk_id=chunk_id,
        topic=topic,
        source_url=f"https://www.rae.es/{topic}",
        content=f"content for chunk {chunk_id}",
        score=score,
    )


@pytest.fixture
def query_embedding():
    return QUERY_EMBEDDING


@pytest.fixture
def make_chunk():
    """Factory fixture -- test modules get `chunk()` without importing conftest."""
    return chunk


@pytest.fixture
def mock_embedding_model():
    embedding_model_service = Mock(spec=IEmbeddingModelService)
    embedding_model_service.embed.return_value = [QUERY_EMBEDDING]
    return embedding_model_service


@pytest.fixture
def mock_chunk_repository():
    return Mock(spec=IChunkRepositoryService)


@pytest.fixture
def mock_strategy():
    """Stands in for DenseVectorStrategy at the seam the service depends on."""
    return Mock(spec=RetrievalStrategy)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def service_factory(mock_embedding_model, mock_chunk_repository, mock_strategy, mock_logging_broker):
    """Builds the service under test, defaulting every injectable stage.

    Fusion defaults to the real PassThroughRankFusion: it is a pure,
    dependency-free ordering no-op, so faking it would only test the fake.
    Tests that need to prove fusion is actually invoked pass a mock.
    """

    def build(strategies=None, fusion=None, filters=None):
        return HybridRetrievalService(
            embedding_model_service=mock_embedding_model,
            chunk_repository_service=mock_chunk_repository,
            strategies=[mock_strategy] if strategies is None else strategies,
            fusion=PassThroughRankFusion() if fusion is None else fusion,
            filters=filters,
            logging_broker=mock_logging_broker,
        )

    return build


@pytest.fixture
def service(service_factory):
    return service_factory()
