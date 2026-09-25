"""Unit tests for ChunkRepositoryService.insert_chunk() -- exception wrapping.

Covers both non-validation tiers _try_catch can produce: the broker-failure
leaf (ChunkRepositoryUnavailableError -> ChunkRepositoryDependencyException)
and the catch-all safety net (ChunkRepositoryServiceException) for anything
_try_catch didn't expect -- exercised here via a genuinely wrong-typed
`topic` (an int rather than str), which reaches `.strip()` inside
`_validate_blank_field` and raises a bare AttributeError that no named
except clause names by type, so it falls through to the final
`except Exception`. See test_insert_chunk_validation.py for the
InvalidChunkRepositoryInputError guards.
"""

import pytest

from rag.models.foundations.chunk_repository.exceptions import (
    ChunkRepositoryDependencyException,
    ChunkRepositoryServiceException,
)

TOPIC = "preterite-vs-imperfect"
SOURCE_URL = "https://www.rae.es/gram/preterito"
CONTENT = "El pretérito indefinido expresa acciones acabadas."
EMBEDDING = [0.1, 0.2, 0.3]
EMBEDDING_MODEL_VERSION = "sentence-transformers/test-model"
CHUNKING_STRATEGY_VERSION = "fixed-800-v1"


class TestChunkRepositoryServiceInsertChunkExceptions:

    def test_should_raise_dependency_exception_when_broker_raises(self, service, mock_broker):
        # given
        mock_broker.insert_chunk.side_effect = RuntimeError("connection refused")

        # when / then
        with pytest.raises(ChunkRepositoryDependencyException) as exc_info:
            service.insert_chunk(
                TOPIC, SOURCE_URL, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
            )

        assert "connection refused" in str(exc_info.value.inner_exception)
        mock_broker.insert_chunk.assert_called_once_with(
            TOPIC, SOURCE_URL, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
        )

    def test_should_raise_service_exception_when_an_unrecognised_error_occurs(self, service, mock_broker):
        # given -- a non-string topic reaches `.strip()` in validation and
        # raises AttributeError, a type _try_catch has no named handler for
        with pytest.raises(ChunkRepositoryServiceException) as exc_info:
            service.insert_chunk(
                123, SOURCE_URL, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
            )

        assert isinstance(exc_info.value.inner_exception, AttributeError)
        mock_broker.insert_chunk.assert_not_called()
