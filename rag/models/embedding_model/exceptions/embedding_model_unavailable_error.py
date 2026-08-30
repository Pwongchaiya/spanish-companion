"""Leaf dependency exception raised when the broker call fails."""

from rag.errors import RagError


class EmbeddingModelUnavailableError(RagError):
    """Raised when the embedding model broker is unreachable or fails.

    Mirrors rag/models/ingestion/exceptions/ingestion_unavailable_error.py's
    shape and its one raise site pattern: caught at the single broker call
    site inside _embed (`self._embedding_model.embed(texts)`), same
    `try: ... except Exception as e: raise EmbeddingModelUnavailableError(str(e)) from e`
    wrap used at Ingestion's and Retrieval's embed-call sites.

    Leaf exception -- always caught and wrapped into
    EmbeddingModelDependencyException before leaving the service.
    """
