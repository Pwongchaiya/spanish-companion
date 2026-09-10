"""Validation checks for HybridRetrievalOrchestrationService.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Validations.cs:12-30 — a named
`Validate<Thing>Input...` aggregator (Validations.cs:12-17) calling one named
per-field check each (the `IsInvalid` overloads, Validations.cs:20-30), rather
than the checks being inlined into the service method's body.

This file did not exist before H5
(Projects/spanish-companion/decisions/architecture-conformance-audit-2026-09-10.md).
The checks lived inline in `retrieve()` and raised a bare `ValueError` from
*outside* `_try_catch`, on the argument that Review only ever passes a
validated `flag.corrected` and an env-configured `top_k`, so a bad input was a
programming error rather than a condition a caller handles. That argument was
wrong in one respect that mattered: an unrecognised exception type still had to
go somewhere, and where it went was Review's catch-all and then an unmapped
HTTP 500. A typed leaf costs one file and buys the 400.

Cited divergence: the reference's rule/accumulator machinery
(`Validate(params (Rule, Parameter)[])`, `UpsertDataList`,
`ThrowIfContainsErrors`, Validations.cs:32-50) is collapsed to a plain
`if condition: raise LeafException(message)` — the same collapse Ingestion,
Session Lifecycle, and Review already made.
"""

from rag.models.orchestrations.retrieval.exceptions import RetrievalValidationError


class HybridRetrievalOrchestrationServiceValidations:
    """Mixin: raises the leaf validation exception when input is unusable.

    See retrieval_service_exceptions.py for how these get wrapped and logged
    before leaving the service.
    """

    def _validate_retrieve_input(self, query: str, top_k: int) -> None:
        """Mirrors ValidateEntitlementCodeInputOnRedeem, Validations.cs:12-17."""
        self._validate_query(query)
        self._validate_top_k(top_k)

    def _validate_query(self, query: str) -> None:
        """Mirrors the `IsInvalid(string text)` overload, Validations.cs:26-30."""
        if not query or not query.strip():
            raise RetrievalValidationError("query is required")

    def _validate_top_k(self, top_k: int) -> None:
        """No direct reference overload — the reference's numeric checks are
        entity-specific; the shape (one named check, one leaf raise) is the same."""
        if top_k < 1:
            raise RetrievalValidationError(f"top_k must be at least 1, got {top_k}")
