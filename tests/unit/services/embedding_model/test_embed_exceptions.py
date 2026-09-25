"""Unit tests for EmbeddingModelService.embed() -- exception wrapping.

Covers both non-validation tiers _try_catch can produce: the broker-failure
leaf (EmbeddingModelUnavailableError -> EmbeddingModelDependencyException)
and the catch-all safety net (EmbeddingModelServiceException) -- exercised
here via a non-string element in `texts` (an int rather than str), which
reaches `.strip()` inside `_validate_embed_input`'s loop and raises a bare
AttributeError that no named except clause names by type, so it falls
through to the final `except Exception`. See test_embed_validation.py for
the InvalidEmbeddingModelInputError guards.
"""

import pytest

from rag.models.foundations.embedding_model.exceptions import (
    EmbeddingModelDependencyException,
    EmbeddingModelServiceException,
)


class TestEmbeddingModelServiceEmbedExceptions:

    def test_should_raise_dependency_exception_when_broker_raises(self, service, mock_broker):
        # given
        mock_broker.embed.side_effect = RuntimeError("model failed to load")

        # when / then
        with pytest.raises(EmbeddingModelDependencyException) as exc_info:
            service.embed(["ser vs estar"])

        assert "model failed to load" in str(exc_info.value.inner_exception)
        mock_broker.embed.assert_called_once_with(["ser vs estar"])

    def test_should_raise_service_exception_when_an_unrecognised_error_occurs(self, service, mock_broker):
        # given -- a non-string element reaches `.strip()` in validation and
        # raises AttributeError, a type _try_catch has no named handler for
        with pytest.raises(EmbeddingModelServiceException) as exc_info:
            service.embed(["ser vs estar", 123])

        assert isinstance(exc_info.value.inner_exception, AttributeError)
        mock_broker.embed.assert_not_called()
