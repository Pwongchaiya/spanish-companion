"""Unit tests for ChunkRepositoryService.search_by_text() -- validation guards."""

import pytest

from rag.models.foundations.chunk_repository.exceptions import (
    ChunkRepositoryValidationException,
    InvalidChunkRepositoryInputError,
)


class TestChunkRepositoryServiceSearchByTextValidation:

    @pytest.mark.parametrize("invalid_top_k", [0, -1])
    def test_should_raise_validation_exception_when_top_k_is_below_one(self, service, mock_broker, invalid_top_k):
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.search_by_text("pretérito", top_k=invalid_top_k)

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.search_by_text.assert_not_called()

    @pytest.mark.parametrize("blank_query", ["", "   "])
    def test_should_raise_validation_exception_when_query_is_blank(self, service, mock_broker, blank_query):
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.search_by_text(blank_query, top_k=3)

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.search_by_text.assert_not_called()
