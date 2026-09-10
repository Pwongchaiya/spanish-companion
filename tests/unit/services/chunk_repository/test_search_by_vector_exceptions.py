"""Unit tests for ChunkRepositoryService.search_by_vector() -- broker failure.

Only the dependency tier is exercised here -- the catch-all safety net
(ChunkRepositoryServiceException) is shared _try_catch mixin code already
covered via test_insert_chunk_exceptions.py's unrecognised-error case, so it
is not duplicated per method.
"""

import pytest

from rag.models.foundations.chunk_repository.exceptions import ChunkRepositoryDependencyException

EMBEDDING = [0.1, 0.2, 0.3]


class TestChunkRepositoryServiceSearchByVectorExceptions:

    def test_should_raise_dependency_exception_when_broker_raises(self, service, mock_broker):
        # given
        mock_broker.search_by_vector.side_effect = RuntimeError("pgvector timeout")

        # when / then
        with pytest.raises(ChunkRepositoryDependencyException) as exc_info:
            service.search_by_vector(EMBEDDING, top_k=5)

        assert "pgvector timeout" in str(exc_info.value.inner_exception)
        mock_broker.search_by_vector.assert_called_once_with(EMBEDDING, 5)
