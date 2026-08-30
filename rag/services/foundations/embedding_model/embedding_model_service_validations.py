"""Validation checks for EmbeddingModelService.

Mirrors rag/services/ingestion/ingestion_service_validations.py's shape one
layer down: a named `_validate_<method>_input` method, collapsed to
`if condition: raise LeafException(message)` rather than the reference's
rule/accumulator machinery -- same collapse Ingestion/Retrieval/Session
Lifecycle/Review already made. `embed` has one input to check (`texts`), so
there is no separate aggregator method here the way Ingestion's two-field
`_validate_ingest_topic_input` needed one.
"""

from typing import List

from rag.models.embedding_model.exceptions import InvalidEmbeddingModelInputError


class EmbeddingModelServiceValidations:
    """Mixin: raises the leaf validation exception when input is unusable."""

    def _validate_embed_input(self, texts: List[str]) -> None:
        if not texts:
            raise InvalidEmbeddingModelInputError("texts is required")

        for text in texts:
            if not text or not text.strip():
                raise InvalidEmbeddingModelInputError("texts must not contain blank entries")
