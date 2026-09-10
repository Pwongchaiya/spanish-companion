"""Unit tests for IngestionService.ingest_topic() -- chunk/embed/insert flow.

See test_ingest_topic_validation.py for the ValueError contracts (blank topic
or source_url, and the strict-zip length mismatch).
"""

from unittest.mock import call

from rag.services.orchestrations.ingestion import CHUNKING_STRATEGY_VERSION

# Must match conftest.py's mock_configuration_broker fixture -- the fixed
# chunk size that fixture hands the service in place of a real env read.
from tests.unit.services.ingestion.conftest import CHUNK_SIZE

TOPIC = "preterite-vs-imperfect"
SOURCE_URL = "https://www.rae.es/gram/preterito"


class TestIngestionServiceIngestTopicLogic:

    def test_should_embed_in_one_batch_and_insert_every_chunk_when_text_has_multiple_chunks(
        self, service, mock_chunk_repository, mock_embedding_model
    ):
        # given -- exactly two distinct chunks: a full-size slice, then a short remainder
        first_chunk = "a" * CHUNK_SIZE
        second_chunk = "bbb"
        text = first_chunk + second_chunk
        mock_embedding_model.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_embedding_model.model_name = "sentence-transformers/test-model"

        # when
        rows_inserted = service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text=text)

        # then
        assert rows_inserted == 2
        mock_embedding_model.embed.assert_called_once_with([first_chunk, second_chunk])
        assert mock_chunk_repository.insert_chunk.call_count == 2
        assert mock_chunk_repository.insert_chunk.call_args_list == [
            call(
                topic=TOPIC,
                source_url=SOURCE_URL,
                content=first_chunk,
                embedding=[0.1, 0.2],
                embedding_model_version="sentence-transformers/test-model",
                chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
            ),
            call(
                topic=TOPIC,
                source_url=SOURCE_URL,
                content=second_chunk,
                embedding=[0.3, 0.4],
                embedding_model_version="sentence-transformers/test-model",
                chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
            ),
        ]

    def test_should_return_zero_and_touch_no_broker_when_text_is_empty(
        self, service, mock_chunk_repository, mock_embedding_model
    ):
        # when
        rows_inserted = service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text="")

        # then
        assert rows_inserted == 0
        mock_embedding_model.embed.assert_not_called()
        mock_chunk_repository.insert_chunk.assert_not_called()

    def test_should_return_zero_and_touch_no_broker_when_text_is_whitespace_only(
        self, service, mock_chunk_repository, mock_embedding_model
    ):
        # when
        rows_inserted = service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text="   \n\t  ")

        # then
        assert rows_inserted == 0
        mock_embedding_model.embed.assert_not_called()
        mock_chunk_repository.insert_chunk.assert_not_called()

    def test_should_insert_once_when_two_chunks_are_byte_identical(
        self, service, mock_chunk_repository, mock_embedding_model
    ):
        # given -- 2 * CHUNK_SIZE identical characters splits into two identical chunks,
        # which dict.fromkeys collapses to one before anything is embedded or inserted
        chunk = "a" * CHUNK_SIZE
        mock_embedding_model.embed.return_value = [[0.1, 0.2]]
        mock_embedding_model.model_name = "sentence-transformers/test-model"

        # when
        rows_inserted = service.ingest_topic(topic=TOPIC, source_url=SOURCE_URL, text=chunk * 2)

        # then
        assert rows_inserted == 1
        mock_embedding_model.embed.assert_called_once_with([chunk])
        mock_chunk_repository.insert_chunk.assert_called_once_with(
            topic=TOPIC,
            source_url=SOURCE_URL,
            content=chunk,
            embedding=[0.1, 0.2],
            embedding_model_version="sentence-transformers/test-model",
            chunking_strategy_version=CHUNKING_STRATEGY_VERSION,
        )
