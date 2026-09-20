"""Unit tests for ChunkRepositoryService.search_by_text() -- happy path."""


class TestChunkRepositoryServiceSearchByTextLogic:

    def test_should_return_brokers_scored_chunks_when_search_succeeds(self, service, mock_broker, chunk):
        # given
        mock_broker.search_by_text.return_value = [chunk]

        # when
        result = service.search_by_text("pretérito indefinido", top_k=5)

        # then
        assert result == [chunk]
        mock_broker.search_by_text.assert_called_once_with("pretérito indefinido", 5)

    def test_should_return_empty_list_when_no_chunks_match(self, service, mock_broker):
        # given
        mock_broker.search_by_text.return_value = []

        # when
        result = service.search_by_text("nada", top_k=5)

        # then
        assert result == []
        mock_broker.search_by_text.assert_called_once_with("nada", 5)
