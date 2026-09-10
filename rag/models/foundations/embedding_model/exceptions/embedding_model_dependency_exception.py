"""Exposure-tier exception wrapping a failed dependency call."""

from rag.errors import RagError


class EmbeddingModelDependencyException(RagError):
    """Wraps EmbeddingModelUnavailableError -- the broker this service depends on failed.

    Mirrors rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_dependency_exception.py's
    shape and its two cited divergences from the reference project, unchanged
    one layer down at the Foundation tier:

    1. No DependencyValidation tier -- there is no layer beneath a Foundation
       service to bubble a rejected input up from; a broker failure here is
       always an infrastructure outage, never a rejected input.
    2. EmbeddingModelUnavailableError IS the leaf (raised directly at the one
       broker call site in _embed), so it is carried through whole as
       inner_exception rather than unwrapped one level.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Embedding model dependency error occurred. Contact support.", inner_exception)
