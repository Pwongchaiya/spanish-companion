"""Unit tests for ChunkRepositoryService.search_by_vector() -- validation guard.

A top_k below 1 would otherwise ask the broker for zero (or a negative
count of) rows, so it is refused before the broker is touched.
"""

import pytest

from rag.models.foundations.chunk_repository.exceptions import (
    ChunkRepositoryValidationException,
    InvalidChunkRepositoryInputError,
)

EMBEDDING = [0.1, 0.2, 0.3]


class TestChunkRepositoryServiceSearchByVectorValidation:

    @pytest.mark.parametrize("invalid_top_k", [0, -1])
    def test_should_raise_validation_exception_when_top_k_is_below_one(
        self, service, mock_broker, invalid_top_k
    ):
        # when / then
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.search_by_vector(EMBEDDING, top_k=invalid_top_k)

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.search_by_vector.assert_not_called()
