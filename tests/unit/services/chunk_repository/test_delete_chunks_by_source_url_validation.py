"""Unit tests for ChunkRepositoryService.delete_chunks_by_source_url() -- validation guards."""

import pytest

from rag.models.foundations.chunk_repository.exceptions import (
    ChunkRepositoryValidationException,
    InvalidChunkRepositoryInputError,
)


class TestChunkRepositoryServiceDeleteChunksBySourceUrlValidation:

    @pytest.mark.parametrize("blank_url", ["", "   "])
    def test_should_raise_validation_exception_when_source_url_is_blank(self, service, mock_broker, blank_url):
        with pytest.raises(ChunkRepositoryValidationException) as exc_info:
            service.delete_chunks_by_source_url(blank_url)

        assert isinstance(exc_info.value.inner_exception, InvalidChunkRepositoryInputError)
        mock_broker.delete_chunks_by_source_url.assert_not_called()
