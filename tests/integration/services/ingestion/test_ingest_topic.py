"""Integration tests for IngestionOrchestrationService against a real test Postgres.

Real SqlAlchemyChunkRepositoryBroker (tests/integration/conftest.py's
`chunk_repository` fixture, TEST_DATABASE_URL, truncated per test), wrapped in
the real ChunkRepositoryService that IngestionOrchestrationService now depends on;
EmbeddingModelBroker mocked -- it is a local sentence-transformers model, so it
falls under CLAUDE.md's "external APIs mocked at the Broker boundary" rule for
the same reason a network API does: loading it makes the test slow and
non-deterministic without exercising any of this service's logic. The mock
stays at the *broker* boundary, with the real EmbeddingModelService wrapped
around it, so this tier still exercises the Foundation layer Ingestion calls
through.

What this tier buys over the unit tier: proof that the SQLAlchemy mapping and
the pgvector round-trip actually work -- rows written by ingest_topic come back
out of Postgres through search_by_vector with the right content.
"""

from unittest.mock import Mock

import pytest

from rag.brokers.chunk_repository import EMBEDDING_DIM
from rag.brokers.configuration import ConfigurationBroker
from rag.brokers.embedding_model import EmbeddingModelBroker
from rag.brokers.logging import StdlibLoggingBroker
from rag.services.foundations.chunk_repository import ChunkRepositoryService
from rag.services.foundations.embedding_model import EmbeddingModelService
from rag.services.orchestrations.ingestion import IngestionOrchestrationService

TOPIC = "preterite-vs-imperfect"

# Fixed chunk size handed to the service through a stubbed ConfigurationBroker
# (H1's testability seam) instead of a real env read -- deterministic no
# matter what the CHUNK_SIZE env knob is set to locally.
CHUNK_SIZE = 800
SOURCE_URL = "https://www.rae.es/gram/preterito"

# Two orthogonal unit vectors, so cosine distance orders the rows unambiguously.
FIRST_EMBEDDING = [1.0] + [0.0] * (EMBEDDING_DIM - 1)
SECOND_EMBEDDING = [0.0] * (EMBEDDING_DIM - 1) + [1.0]

# Padded with '.' rather than spaces so chunk_text's .strip() leaves the slice intact.
FIRST_CHUNK = "El pretérito indefinido expresa acciones acabadas.".ljust(CHUNK_SIZE, ".")
SECOND_CHUNK = "El imperfecto describe acciones habituales."


@pytest.fixture
def mock_embedding_model():
    broker = Mock(spec=EmbeddingModelBroker)
    broker.embed.return_value = [FIRST_EMBEDDING, SECOND_EMBEDDING]
    broker.model_name = "sentence-transformers/test-model"
    return broker


@pytest.fixture
def mock_configuration_broker():
    broker = Mock(spec=ConfigurationBroker)
    broker.get.return_value = str(CHUNK_SIZE)
    return broker


@pytest.fixture
def service(chunk_repository, mock_embedding_model, mock_configuration_broker):
    logging_broker = StdlibLoggingBroker()
    return IngestionOrchestrationService(
        chunk_repository_service=ChunkRepositoryService(chunk_repository, logging_broker=logging_broker),
        embedding_model_service=EmbeddingModelService(mock_embedding_model, logging_broker=logging_broker),
        configuration_broker=mock_configuration_broker,
        logging_broker=logging_broker,
    )


class TestIngestionServiceIngestTopicIntegration:

    def test_should_persist_every_chunk_when_ingesting_a_topic(self, service, chunk_repository, mock_embedding_model):
        # given
        text = FIRST_CHUNK + SECOND_CHUNK

        # when
        rows_inserted = service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text=text)

        # then
        assert rows_inserted == 2
        mock_embedding_model.embed.assert_called_once_with([FIRST_CHUNK, SECOND_CHUNK])

        results = chunk_repository.search_by_vector(embedding=FIRST_EMBEDDING, top_k=10)
        assert [result.content for result in results] == [FIRST_CHUNK, SECOND_CHUNK]
        assert {result.topic for result in results} == {TOPIC}
        assert {result.source_url for result in results} == {SOURCE_URL}
        assert all(result.chunk_id is not None for result in results)

    def test_should_write_nothing_when_text_is_whitespace_only(self, service, chunk_repository):
        # when
        rows_inserted = service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text="   \n  ")

        # then
        assert rows_inserted == 0
        assert chunk_repository.search_by_vector(embedding=FIRST_EMBEDDING, top_k=10) == []
