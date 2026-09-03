"""Unit tests for ChunkRepositoryService.search_by_vector() -- happy path.

See test_search_by_vector_validation.py for the top_k guard and
test_search_by_vector_exceptions.py for broker-failure wrapping.
"""

EMBEDDING = [0.1, 0.2, 0.3]


class TestChunkRepositoryServiceSearchByVectorLogic:

    def test_should_return_brokers_scored_chunks_when_search_succeeds(
        self, service, mock_broker, chunk
    ):
        # given
        mock_broker.search_by_vector.return_value = [chunk]

        # when
        result = service.search_by_vector(EMBEDDING, top_k=5)

        # then
        assert result == [chunk]
        mock_broker.search_by_vector.assert_called_once_with(EMBEDDING, 5)

    def test_should_return_empty_list_when_no_chunks_match(self, service, mock_broker):
        # given -- empty is a valid result, not an error
        mock_broker.search_by_vector.return_value = []

        # when
        result = service.search_by_vector(EMBEDDING, top_k=5)

        # then
        assert result == []
        mock_broker.search_by_vector.assert_called_once_with(EMBEDDING, 5)
