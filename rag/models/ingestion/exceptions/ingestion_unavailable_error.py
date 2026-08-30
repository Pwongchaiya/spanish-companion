"""Leaf dependency exception raised when a broker call fails."""

from rag.errors import RagError


class IngestionUnavailableError(RagError):
    """Raised when the chunk store or embedding model is unreachable.

    Name and docstring mirror `RetrievalUnavailableError`
    (rag/services/retrieval/service.py:30-31) exactly -- both features
    depend on the same two brokers (ChunkRepositoryBroker,
    EmbeddingModelBroker) and both need one name for "the infrastructure
    behind them is down", distinct from a legitimate empty/zero result.

    Raised at the two broker call sites in
    _IngestionServiceBase._ingest_topic (`embed`, `insert_chunk`), matching
    RetrievalUnavailableError's two raise sites in `retrieve()`
    (rag/services/retrieval/service.py:89-92 and :100-103).

    Leaf exception -- always caught and wrapped into
    IngestionOrchestrationDependencyException before leaving the service,
    mirroring EntitlementCodesOrchestrationService.Exeptions.cs:53-76
    (every dependency-shaped catch feeds CreateAndLogDependencyException).

    Before this rebuild no name existed for this case at all: SQLAlchemy /
    pgvector / sentence-transformers exceptions propagated raw out of
    ingest_topic. That gap is what CLAUDE.md's Orchestration waiver row
    calls out as "silently never covered by the original waiver".
    """
