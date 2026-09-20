"""Unit tests for ChunkRepositoryService.count_chunks_by_source_url() -- broker failure."""

import pytest

from rag.models.foundations.chunk_repository.exceptions import ChunkRepositoryDependencyException


class TestChunkRepositoryServiceCountChunksBySourceUrlExceptions:

    def test_should_raise_dependency_exception_when_broker_raises(self, service, mock_broker):
        # given
        mock_broker.count_chunks_by_source_url.side_effect = RuntimeError("db down")

        # when / then
        with pytest.raises(ChunkRepositoryDependencyException) as exc_info:
            service.count_chunks_by_source_url("https://www.rae.es/a")

        assert "db down" in str(exc_info.value.inner_exception)
        mock_broker.count_chunks_by_source_url.assert_called_once_with("https://www.rae.es/a")
