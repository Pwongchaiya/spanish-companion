"""Leaf validation exception raised by HybridRetrievalOrchestrationService's input checks."""

from rag.errors import RagError


class RetrievalValidationError(RagError):
    """Raised when retrieval input is unusable.

    Two raise sites, both in retrieval_service_validations.py: a blank
    `query` and a `top_k` below 1. Replaces the bare `ValueError` those two
    checks used to raise (H5 in
    Projects/spanish-companion/decisions/architecture-conformance-audit-2026-09-10.md):
    a framework exception carried no tier, so ReviewOrchestrationService could only
    punt it to its catch-all and the route returned 500 for what is a 400.

    Mirrors NL.Core.Entitlements.Api/Models/Orchestrations/EntitlementCodes/
    InvalidEntitlementCodeOrchestrationException.cs:11-13 -- message-only
    constructor, no innerException, raised from named validation methods
    (EntitlementCodesOrchestrationService.Validations.cs:12-17).

    Leaf exception -- always caught and wrapped into
    RetrievalOrchestrationValidationException before leaving the service,
    mirroring EntitlementCodesOrchestrationService.Exeptions.cs:25-28.

    Name follows its `rag` siblings (`IngestionValidationError`,
    `RetrievalUnavailableError`) rather than the reference's
    `Invalid<Entity>...` form, the same call
    rag/models/orchestrations/ingestion/exceptions/ingestion_validation_error.py records.
    """
