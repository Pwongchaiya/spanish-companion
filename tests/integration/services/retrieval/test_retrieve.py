"""Integration tests for HybridRetrievalService against a real test Postgres.

Per CLAUDE.md's Phase 2 test strategy: real test Postgres (the
`chunk_repository` fixture in tests/integration/conftest.py), external APIs
mocked at the Broker boundary.

What this tier adds over the Unit tier: the Unit tests fake the strategy, so
nothing there proves the pgvector `<=>` cosine-distance query actually orders
and limits rows the way DenseVectorStrategy assumes. Here the service is built
with NO `strategies` override, so the real DenseVectorStrategy and the real
SQL run.

EmbeddingModelBroker stays mocked -- loading the sentence-transformers model
is slow, and a real one would make nearest-neighbour ordering a property of
the model rather than something this test can assert deterministically. The
fixed vectors below are hand-picked so the expected distance order is
arithmetic, not luck.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.chunk_repository import EMBEDDING_DIM
from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.services.retrieval import HybridRetrievalService

EMBEDDING_MODEL_VERSION = "test-model-v1"
CHUNKING_STRATEGY_VERSION = "test-chunking-v1"


def axis_vector(axis: int) -> list[float]:
    """A unit vector along one axis -- orthogonal to every other axis vector."""
    vector = [0.0] * EMBEDDING_DIM
    vector[axis] = 1.0
    return vector


def query_vector(*weights: float) -> list[float]:
    """A query leaning on the leading axes by the given weights.

    Cosine similarity against axis_vector(i) is weights[i] / ||query||, so the
    weights alone fix the expected nearest-first order.
    """
    vector = [0.0] * EMBEDDING_DIM
    vector[: len(weights)] = weights
    return vector


# Leans hardest on axis 0, then axis 1, then axis 2 -- so the expected
# distance order is always ser-vs-estar, preterite-vs-imperfect, subjunctive.
QUERY_EMBEDDING = query_vector(1.0, 0.5, 0.1)

TOPICS_BY_AXIS = ["ser-vs-estar", "preterite-vs-imperfect", "subjunctive-basics"]


@pytest.fixture
def mock_embedding_model():
    broker = Mock(spec=EmbeddingModelBroker)
    broker.embed.return_value = [QUERY_EMBEDDING]
    return broker


@pytest.fixture
def seeded_chunk_ids(chunk_repository):
    """Three chunks, one per leading axis, in TOPICS_BY_AXIS order."""
    return [
        chunk_repository.insert_chunk(
            topic=topic,
            source_url=f"https://www.rae.es/{topic}",
            content=f"RAE grammar text about {topic}",
            embedding=axis_vector(axis),
            embedding_model_version=EMBEDDING_MODEL_VERSION,
            chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
        )
        for axis, topic in enumerate(TOPICS_BY_AXIS)
    ]


@pytest.fixture
def service(mock_embedding_model, chunk_repository):
    # No strategies/fusion/filters override: the real DenseVectorStrategy and
    # the real pgvector query are the point of this tier.
    return HybridRetrievalService(
        embedding_model=mock_embedding_model,
        chunk_repository=chunk_repository,
    )


class TestHybridRetrievalServiceRetrieveIntegration:

    def test_should_return_chunks_nearest_first_by_cosine_distance(
        self, service, mock_embedding_model, seeded_chunk_ids
    ):
        # when
        results = service.retrieve(query="ella es feliz", top_k=3)

        # then -- real pgvector ordering, not a faked strategy's list.
        mock_embedding_model.embed.assert_called_once_with(["ella es feliz"])
        assert [result.chunk_id for result in results] == seeded_chunk_ids
        assert [result.topic for result in results] == TOPICS_BY_AXIS

    def test_should_return_ascending_distances_with_content_and_source_url(
        self, service, seeded_chunk_ids
    ):
        # when
        results = service.retrieve(query="ella es feliz", top_k=3)

        # then -- score is a raw cosine distance (lower = closer), and the row
        # is hydrated well enough for Generation to cite it.
        scores = [result.score for result in results]
        assert scores == sorted(scores)
        assert results[0].source_url == "https://www.rae.es/ser-vs-estar"
        assert results[0].content == "RAE grammar text about ser-vs-estar"

    def test_should_limit_rows_to_top_k(self, service, seeded_chunk_ids):
        # when -- the SQL LIMIT, not just the service's slice.
        results = service.retrieve(query="ella es feliz", top_k=2)

        # then
        assert [result.chunk_id for result in results] == seeded_chunk_ids[:2]

    def test_should_float_category_matching_chunk_ahead_of_nearer_chunks(
        self, service, seeded_chunk_ids
    ):
        # given -- axis 2 is the FURTHEST chunk by cosine distance, so a
        # changed order can only come from the category boost.
        # when
        results = service.retrieve(query="ella es feliz", top_k=3, category="subjunctive")

        # then -- boosted to front, nothing dropped.
        assert [result.chunk_id for result in results] == [
            seeded_chunk_ids[2],
            seeded_chunk_ids[0],
            seeded_chunk_ids[1],
        ]

    def test_should_return_empty_list_when_corpus_is_empty(self, service):
        # given -- the chunk_repository fixture truncates before each test and
        # nothing is seeded here.
        # when
        results = service.retrieve(query="ella es feliz", top_k=3)

        # then -- empty is a valid result, not an error.
        assert results == []
