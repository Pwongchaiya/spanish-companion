"""Unit tests for ChunkRepositoryService.insert_chunk() -- happy path.

See test_insert_chunk_validation.py for the blank-field guards and
test_insert_chunk_exceptions.py for broker-failure wrapping.
"""

TOPIC = "preterite-vs-imperfect"
SOURCE_URL = "https://www.rae.es/gram/preterito"
CONTENT = "El pretérito indefinido expresa acciones acabadas."
EMBEDDING = [0.1, 0.2, 0.3]
EMBEDDING_MODEL_VERSION = "sentence-transformers/test-model"
CHUNKING_STRATEGY_VERSION = "fixed-800-v1"


class TestChunkRepositoryServiceInsertChunkLogic:

    def test_should_return_broker_generated_id_when_insert_succeeds(self, service, mock_broker):
        # given
        mock_broker.insert_chunk.return_value = 42

        # when
        result = service.insert_chunk(
            TOPIC, SOURCE_URL, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
        )

        # then
        assert result == 42
        mock_broker.insert_chunk.assert_called_once_with(
            TOPIC, SOURCE_URL, CONTENT, EMBEDDING, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION
        )

    def test_should_pass_embedding_through_unchanged_when_insert_succeeds(self, service, mock_broker):
        # given -- the service does no transformation on the embedding vector,
        # it is a pure passthrough from caller to broker
        mock_broker.insert_chunk.return_value = 7
        embedding = [0.9, -0.4, 0.0, 0.33]

        # when
        service.insert_chunk(TOPIC, SOURCE_URL, CONTENT, embedding, EMBEDDING_MODEL_VERSION, CHUNKING_STRATEGY_VERSION)

        # then
        (_, _, _, passed_embedding, _, _), _ = mock_broker.insert_chunk.call_args
        assert passed_embedding is embedding
