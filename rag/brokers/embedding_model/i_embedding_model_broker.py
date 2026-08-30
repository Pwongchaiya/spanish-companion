"""EmbeddingModelBroker — external-resource boundary for text embedding."""

from typing import List, Protocol


class EmbeddingModelBroker(Protocol):
    """External-resource boundary for text embedding."""

    @property
    def model_name(self) -> str:
        """The model name this broker is configured to use.

        Used for versioning and mismatch detection: ingestion tags chunks with
        this value, and retrieval checks for consistency at query time.
        """
        ...

    def embed(self, texts: List[str]) -> List[List[float]]:
        """One 384-dim vector per text, same order.

        Ingestion passes a batch of chunk texts; Retrieval passes a
        single-element list and reads result[0].
        """
        ...
