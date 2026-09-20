"""Unit tests for ChunkRepositoryService.count_chunks_by_source_url() -- validation guards."""

import pytest

from rag.models.foundations.chunk_repository.exceptions import (
    ChunkRepositoryValidationException,
    InvalidChunkRepositoryInputError,
)


class TestChunkRepositoryServiceCountChunksBySourceUrlValidation:

    @pytest.mark.parametrize("blank_url", ["", "   "])
    def test_should_raise_validation_exception_when_source_url_is_blank(self, service, mock_broker, blank_url):
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.count_chunks_by_source_url(blank_url)

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.count_chunks_by_source_url.assert_not_called()
