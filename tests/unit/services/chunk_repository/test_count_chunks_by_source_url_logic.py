"""Unit tests for ChunkRepositoryService.count_chunks_by_source_url() -- happy path."""


class TestChunkRepositoryServiceCountChunksBySourceUrlLogic:

    def test_should_return_brokers_count_when_call_succeeds(self, service, mock_broker):
        # given
        mock_broker.count_chunks_by_source_url.return_value = 7

        # when
        result = service.count_chunks_by_source_url("https://www.rae.es/a")

        # then
        assert result == 7
        mock_broker.count_chunks_by_source_url.assert_called_once_with("https://www.rae.es/a")
