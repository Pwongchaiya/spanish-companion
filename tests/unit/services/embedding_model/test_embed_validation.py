"""Unit tests for EmbeddingModelService.embed() -- validation guards.

An empty `texts` list or any blank/whitespace-only element must be refused
before the broker is touched -- otherwise a zero-length batch silently
returns zero vectors, or a blank entry gets embedded as if it were real text.
"""

import pytest

from rag.models.foundations.embedding_model.exceptions import (
    EmbeddingModelValidationException,
    InvalidEmbeddingModelInputError,
)


class TestEmbeddingModelServiceEmbedValidation:

    def test_should_raise_validation_exception_when_texts_is_empty(self, service, mock_broker):
        # when / then
        with pytest.raises(EmbeddingModelValidationException) as exc_info:
            service.embed([])

        assert isinstance(exc_info.value.inner_exception, InvalidEmbeddingModelInputError)
        mock_broker.embed.assert_not_called()

    @pytest.mark.parametrize("blank_text", ["", "   ", "\n\t"])
    def test_should_raise_validation_exception_when_a_text_is_blank(
        self, service, mock_broker, blank_text
    ):
        # when / then
        with pytest.raises(EmbeddingModelValidationException) as exc_info:
            service.embed(["hola", blank_text])

        assert isinstance(exc_info.value.inner_exception, InvalidEmbeddingModelInputError)
        mock_broker.embed.assert_not_called()

    def test_should_check_every_element_not_just_the_first(self, service, mock_broker):
        # given -- the first element is fine; the second is blank
        with pytest.raises(EmbeddingModelValidationException):
            service.embed(["ser vs estar", ""])

        mock_broker.embed.assert_not_called()
