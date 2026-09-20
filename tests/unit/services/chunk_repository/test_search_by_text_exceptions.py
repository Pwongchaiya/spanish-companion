"""Unit tests for ChunkRepositoryService.search_by_text() -- broker failure."""

import pytest

from rag.models.foundations.chunk_repository.exceptions import ChunkRepositoryDependencyException


class TestChunkRepositoryServiceSearchByTextExceptions:

    def test_should_raise_dependency_exception_when_broker_raises(self, service, mock_broker):
        # given
        mock_broker.search_by_text.side_effect = RuntimeError("tsvector timeout")

        # when / then
        with pytest.raises(ChunkRepositoryDependencyException) as exc_info:
            service.search_by_text("pretérito", top_k=5)

        assert "tsvector timeout" in str(exc_info.value.inner_exception)
        mock_broker.search_by_text.assert_called_once_with("pretérito", 5)
