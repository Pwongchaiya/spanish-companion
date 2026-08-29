"""Integration tests for rag.brokers.chunk_repository.SqlAlchemyChunkRepositoryBroker.

Per CLAUDE.md's Phase 2 test strategy: real test Postgres (the `chunk_repository`
fixture in tests/integration/conftest.py, TEST_DATABASE_URL), no mocks.

What this tier proves: the pgvector cosine-distance query actually orders rows
nearest-first, respects top_k limits, and round-trips embeddings correctly against
a real database. The embedding dimensions and data types (384-dim float lists)
work as expected with SQLAlchemy + pgvector.
"""

import pytest

from rag.brokers.chunk_repository import EMBEDDING_DIM
from rag.models.retrieval import ScoredChunk


def axis_vector(axis: int) -> list[float]:
    """A unit vector along one axis -- orthogonal to every other axis vector.

    Used to create deterministic cosine-distance ordering independent of
    actual embedding content.
    """
    vector = [0.0] * EMBEDDING_DIM
    vector[axis] = 1.0
    return vector


def weighted_vector(weights: list[float]) -> list[float]:
    """A vector with given weights along leading axes, rest zero.

    Used to create a clear distance ordering: cos(weighted_vector, axis_vector(i))
    is proportional to weights[i], so weights alone fix the expected order.
    """
    vector = [0.0] * EMBEDDING_DIM
    for i, weight in enumerate(weights):
        vector[i] = weight
    return vector


class TestSqlAlchemyChunkRepositoryBrokerInsertChunk:
    """Tests for ChunkRepositoryBroker.insert_chunk()."""

    def test_should_return_generated_id_when_inserting_chunk(self, chunk_repository):
        # when
        chunk_id = chunk_repository.insert_chunk(
            topic="ser-vs-estar",
            source_url="https://www.rae.es/ser-estar",
            content="El verbo ser...",
            embedding=axis_vector(0),
            embedding_model_version="test-model-v1",
            chunking_strategy_version="test-chunking-v1",
        )

        # then
        assert isinstance(chunk_id, int)
        assert chunk_id > 0

    def test_should_round_trip_chunk_data_through_database(self, chunk_repository):
        # given
        topic = "preterite-vs-imperfect"
        source_url = "https://www.rae.es/preterito"
        content = "El pretérito expresa..."
        embedding = axis_vector(1)
        model_version = "multilingual-v1"
        chunking_version = "chunk-v1"

        # when
        inserted_id = chunk_repository.insert_chunk(
            topic=topic,
            source_url=source_url,
            content=content,
            embedding=embedding,
            embedding_model_version=model_version,
            chunking_strategy_version=chunking_version,
        )

        # then -- retrieve it back via search and verify all fields survive
        results = chunk_repository.search_by_vector(embedding=embedding, top_k=1)
        assert len(results) == 1
        result = results[0]
        assert result.chunk_id == inserted_id
        assert result.topic == topic
        assert result.source_url == source_url
        assert result.content == content

    def test_should_accept_embedding_with_correct_dimension(self, chunk_repository):
        # given -- exactly EMBEDDING_DIM elements
        correct_embedding = axis_vector(2)
        assert len(correct_embedding) == EMBEDDING_DIM

        # when/then -- no error
        chunk_id = chunk_repository.insert_chunk(
            topic="test",
            source_url="https://test.com",
            content="test",
            embedding=correct_embedding,
            embedding_model_version="v1",
            chunking_strategy_version="v1",
        )
        assert chunk_id > 0


class TestSqlAlchemyChunkRepositoryBrokerSearchByVector:
    """Tests for ChunkRepositoryBroker.search_by_vector()."""

    @pytest.fixture
    def three_chunks(self, chunk_repository):
        """Insert three orthogonal chunks for deterministic distance ordering."""
        return [
            chunk_repository.insert_chunk(
                topic=f"topic-{i}",
                source_url=f"https://test.com/topic-{i}",
                content=f"Content for topic {i}",
                embedding=axis_vector(i),
                embedding_model_version="test-v1",
                chunking_strategy_version="test-v1",
            )
            for i in range(3)
        ]

    def test_should_return_empty_list_when_corpus_is_empty(self, chunk_repository):
        # when
        results = chunk_repository.search_by_vector(embedding=axis_vector(0), top_k=10)

        # then
        assert results == []

    def test_should_return_chunks_nearest_first_by_cosine_distance(
        self, chunk_repository, three_chunks
    ):
        # given -- query leans hardest on axis 0 (weight 1.0), then 1 (0.5), then 2 (0.25)
        # This produces clear distance ordering: nearest to axis_vector(0), then (1), then (2)
        query = weighted_vector([1.0, 0.5, 0.25])

        # when
        results = chunk_repository.search_by_vector(embedding=query, top_k=3)

        # then -- ordered by cosine distance (lower distance = closer = nearest first)
        # cosine(query, axis_vector(i)) ∝ weights[i], so order is by weight magnitude
        assert [r.chunk_id for r in results] == three_chunks
        assert results[0].topic == "topic-0"
        assert results[1].topic == "topic-1"
        assert results[2].topic == "topic-2"

    def test_should_return_scores_in_ascending_distance_order(
        self, chunk_repository, three_chunks
    ):
        # when -- query weighted to clearly distinguish all chunks
        query = weighted_vector([1.0, 0.5, 0.25])
        results = chunk_repository.search_by_vector(embedding=query, top_k=3)

        # then -- scores are raw cosine distances (lower = closer)
        scores = [r.score for r in results]
        assert scores == sorted(scores)
        # First result (axis_vector(0)) has lowest distance to the weighted query
        assert scores[0] <= scores[1] <= scores[2]

    def test_should_respect_top_k_limit(self, chunk_repository, three_chunks):
        # when
        query = weighted_vector([1.0, 0.5, 0.25])
        results = chunk_repository.search_by_vector(embedding=query, top_k=2)

        # then
        assert len(results) == 2
        assert [r.chunk_id for r in results] == three_chunks[:2]

    def test_should_return_full_scored_chunk_with_all_fields(
        self, chunk_repository, three_chunks
    ):
        # when
        query = weighted_vector([1.0, 0.5, 0.25])
        results = chunk_repository.search_by_vector(embedding=query, top_k=1)

        # then
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, ScoredChunk)
        assert result.chunk_id == three_chunks[0]
        assert result.topic == "topic-0"
        assert result.source_url == "https://test.com/topic-0"
        assert result.content == "Content for topic 0"
        assert isinstance(result.score, float)

    def test_should_return_chunks_up_to_top_k_when_fewer_exist(
        self, chunk_repository, three_chunks
    ):
        # when -- request top_k=10 but only 3 chunks exist
        query = weighted_vector([1.0, 0.5, 0.25])
        results = chunk_repository.search_by_vector(embedding=query, top_k=10)

        # then -- return all 3
        assert len(results) == 3

    def test_should_handle_zero_top_k(self, chunk_repository, three_chunks):
        # when
        query = weighted_vector([1.0, 0.5, 0.25])
        results = chunk_repository.search_by_vector(embedding=query, top_k=0)

        # then
        assert results == []

    def test_should_return_deterministic_order_for_same_query(
        self, chunk_repository, three_chunks
    ):
        # given
        query = weighted_vector([1.0, 0.5, 0.25])

        # when
        results1 = chunk_repository.search_by_vector(embedding=query, top_k=3)
        results2 = chunk_repository.search_by_vector(embedding=query, top_k=3)

        # then
        assert [r.chunk_id for r in results1] == [r.chunk_id for r in results2]
