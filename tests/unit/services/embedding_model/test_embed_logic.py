"""Unit tests for EmbeddingModelService.embed() -- happy path.

See test_embed_validation.py for the blank/empty-input guards and
test_embed_exceptions.py for broker-failure wrapping.
"""


class TestEmbeddingModelServiceEmbedLogic:

    def test_should_return_brokers_vectors_when_embed_succeeds(self, service, mock_broker):
        # given
        mock_broker.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

        # when
        result = service.embed(["hola", "adios"])

        # then
        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_broker.embed.assert_called_once_with(["hola", "adios"])

    def test_should_embed_a_single_text_when_given_one_element_list(self, service, mock_broker):
        # given -- Retrieval's call shape: a single-element query list
        mock_broker.embed.return_value = [[0.9, -0.1]]

        # when
        result = service.embed(["ser vs estar"])

        # then
        assert result == [[0.9, -0.1]]
        mock_broker.embed.assert_called_once_with(["ser vs estar"])
