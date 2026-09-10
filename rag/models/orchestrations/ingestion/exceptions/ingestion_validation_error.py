"""Leaf validation exception raised by IngestionOrchestrationService's input checks."""

from rag.errors import RagError


class IngestionValidationError(RagError):
    """Raised when ingestion input is unusable.

    Three raise sites, all in ingestion_service_validations.py: blank
    `topic`, blank `source_url`, and an embedding batch whose length does
    not match the chunk batch it was supposed to describe.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    InvalidEntitlementCodeOrchestrationException.cs:11-13 -- message-only
    constructor, no innerException, raised from named validation methods
    (EntitlementCodesOrchestrationService.Validations.cs:12-17).

    Leaf exception -- always caught and wrapped into
    IngestionOrchestrationValidationException before leaving the service,
    mirroring EntitlementCodesOrchestrationService.Exeptions.cs:25-28.

    Cited naming divergence: the Review rebuild renamed its leaf
    `FlagNotFoundException` -> `NotFoundFlagException` to match the
    reference's `<Condition><Entity>` convention
    (NL.Core.Entitlements.Api/Models/Foundations/Entitlements/Exceptions/
    NotFoundEntitlementException.cs). This class keeps its existing
    `IngestionValidationError` name: CLAUDE.md's Orchestration waiver row
    already pins it by name as Ingestion's one custom exception, and it is
    the name `RetrievalUnavailableError` is a sibling of within `rag`.
    Only its module path changed in this rebuild.
    """
