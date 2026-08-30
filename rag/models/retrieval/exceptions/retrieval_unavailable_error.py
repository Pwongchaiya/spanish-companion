"""Leaf dependency exception: the retrieval pipeline's backing resources are down."""

from rag.errors import RagError


class RetrievalUnavailableError(RagError):
    """Raised when the chunk store or embedding model is unreachable.

    Leaf exception -- always caught and wrapped into
    RetrievalOrchestrationDependencyException before leaving this service,
    mirroring EntitlementCodesOrchestrationService.Exeptions.cs:53-76, where
    every recognised dependency failure is funnelled through
    CreateAndLogDependencyException rather than escaping raw.

    Name kept verbatim from the pre-rebuild
    `rag/services/retrieval/service.py:30-31`, unlike Review's
    FlagNotFoundException -> NotFoundFlagException rename: this is an
    infrastructure-availability condition, not a `<Condition><Entity>`
    validation leaf, so the reference's NotFoundEntitlementException.cs
    naming convention does not apply to it. Its nearest reference analog is
    FailedEntitlementStorageException.cs (Models/Foundations/Entitlements/
    Exceptions/), which is likewise named for the failure, not an entity
    state.

    Both raise sites are unchanged: EmbeddingModelBroker.embed() failing,
    and a RetrievalStrategy.search() failing (retrieval_service.py).
    """
