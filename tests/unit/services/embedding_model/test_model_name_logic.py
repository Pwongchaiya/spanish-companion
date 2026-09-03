"""Unit test for EmbeddingModelService.model_name -- pure passthrough.

No validation/exceptions file for this one: the property has no failure mode
of its own to wrap (see the `ponytail:` comment on the property itself), so
it is not routed through `_try_catch`.
"""


class TestEmbeddingModelServiceModelNameLogic:

    def test_should_return_brokers_model_name_unchanged(self, service, mock_broker):
        # given
        mock_broker.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

        # when
        result = service.model_name

        # then
        assert result == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
