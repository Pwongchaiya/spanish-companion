"""Unit tests for IngestionOrchestrationService.ingest_topic() -- ValueError contracts.

Writes to `chunks` are one-way (the broker has no delete path), so a blank
topic/source_url must be refused before either broker is touched. The
embeddings/chunks length check lives here too: it is the guard that stops a
mismatched embeddings list from either silently truncating the insert loop
or leaving partial rows behind -- checked before the loop starts, so a
mismatch inserts zero rows, not some.
"""

import pytest

from rag.models.orchestrations.ingestion.exceptions import (
    IngestionOrchestrationValidationException,
    IngestionValidationError,
)

# Must match conftest.py's mock_configuration_broker fixture -- the fixed
# chunk size that fixture hands the service in place of a real env read.
from tests.unit.services.ingestion.conftest import CHUNK_SIZE

TOPIC = "preterite-vs-imperfect"
SOURCE_URL = "https://www.rae.es/gram/preterito"
TEXT = "El pretérito indefinido expresa acciones acabadas."


class TestIngestionServiceIngestTopicValidation:

    @pytest.mark.parametrize("blank_topic", ["", "   ", "\n\t"])
    def test_should_raise_value_error_before_touching_brokers_when_topic_is_blank(
        self, service, mock_chunk_repository, mock_embedding_model, blank_topic
    ):
        # when / then
        with pytest.raises(IngestionOrchestrationValidationException) as exc_info:
            service.ingest_topic(topic=blank_topic, source_url=SOURCE_URL, text=TEXT)

        assert isinstance(exc_info.value.inner_exception, IngestionValidationError)

        mock_embedding_model.embed.assert_not_called()
        mock_chunk_repository.insert_chunk.assert_not_called()

    @pytest.mark.parametrize("blank_source_url", ["", "   ", "\n\t"])
    def test_should_raise_value_error_before_touching_brokers_when_source_url_is_blank(
        self, service, mock_chunk_repository, mock_embedding_model, blank_source_url
    ):
        # when / then
        with pytest.raises(IngestionOrchestrationValidationException) as exc_info:
            service.ingest_topic(topic=TOPIC, source_url=blank_source_url, text=TEXT)

        assert isinstance(exc_info.value.inner_exception, IngestionValidationError)

        mock_embedding_model.embed.assert_not_called()
        mock_chunk_repository.insert_chunk.assert_not_called()

    def test_should_raise_value_error_when_embeddings_are_fewer_than_chunks(
        self, service, mock_chunk_repository, mock_embedding_model
    ):
        # given -- two chunks, one embedding: checked before the insert loop
        # starts, so nothing is written for a batch that doesn't line up
        text = "a" * CHUNK_SIZE + "bbb"
        mock_embedding_model.embed.return_value = [[0.1, 0.2]]

        # when / then
        with pytest.raises(IngestionOrchestrationValidationException) as exc_info:
            service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text=text)

        assert isinstance(exc_info.value.inner_exception, IngestionValidationError)

        mock_embedding_model.embed.assert_called_once_with(["a" * CHUNK_SIZE, "bbb"])
        mock_chunk_repository.insert_chunk.assert_not_called()

    def test_should_raise_value_error_when_embeddings_are_more_than_chunks(
        self, service, mock_chunk_repository, mock_embedding_model
    ):
        # given -- one chunk, two embeddings: the extra vector means the batch no
        # longer lines up with the chunks it was supposed to describe
        mock_embedding_model.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

        # when / then
        with pytest.raises(IngestionOrchestrationValidationException) as exc_info:
            service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text=TEXT)

        assert isinstance(exc_info.value.inner_exception, IngestionValidationError)

        mock_embedding_model.embed.assert_called_once_with([TEXT])
        mock_chunk_repository.insert_chunk.assert_not_called()
