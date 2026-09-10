"""Unit tests for ChunkRepositoryService.insert_chunk() -- validation guards.

Writes to `chunks` are one-way (the broker has no delete path per this
service's own module docstring), so a blank topic/source_url/content must be
refused before the broker is ever touched.
"""

import pytest

from rag.models.foundations.chunk_repository.exceptions import (
    ChunkRepositoryValidationException,
    InvalidChunkRepositoryInputError,
)

TOPIC = "preterite-vs-imperfect"
SOURCE_URL = "https://www.rae.es/gram/preterito"
CONTENT = "El pretérito indefinido expresa acciones acabadas."
EMBEDDING = [0.1, 0.2, 0.3]
EMBEDDING_MODEL_VERSION = "sentence-transformers/test-model"
CHUNKING_STRATEGY_VERSION = "fixed-800-v1"


class TestChunkRepositoryServiceInsertChunkValidation:

    @pytest.mark.parametrize("blank_topic", ["", "   ", "\n\t"])
    def test_should_raise_validation_exception_when_topic_is_blank(
        self, service, mock_broker, blank_topic
    ):
        # when / then
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.insert_chunk(
                blank_topic, SOURCE_URL, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
            )

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.insert_chunk.assert_not_called()

    @pytest.mark.parametrize("blank_source_url", ["", "   ", "\n\t"])
    def test_should_raise_validation_exception_when_source_url_is_blank(
        self, service, mock_broker, blank_source_url
    ):
        # when / then
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.insert_chunk(
                TOPIC, blank_source_url, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
            )

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.insert_chunk.assert_not_called()

    @pytest.mark.parametrize("blank_content", ["", "   ", "\n\t"])
    def test_should_raise_validation_exception_when_content_is_blank(
        self, service, mock_broker, blank_content
    ):
        # when / then
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.insert_chunk(
                TOPIC, SOURCE_URL, blank_content, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
            )

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.insert_chunk.assert_not_called()

    def test_should_check_topic_before_source_url_and_content(self, service, mock_broker):
        # given -- all three fields blank; topic is checked first, so its
        # message is the one the caller sees
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.insert_chunk(
                "", "", "", EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
            )

        assert "topic is required" in str(exc_info.value.inner_exception)
        mock_broker.insert_chunk.assert_not_called()
