"""Validation checks for IngestionService.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Validations.cs:12-30 — a named
`Validate<Thing>Input...` aggregator (Validations.cs:12-17) calling one named
per-field check each (the `IsInvalid` overloads, Validations.cs:20-30), rather
than the checks being inlined into the service method's body.

Cited divergence: the reference's rule/accumulator machinery
(`Validate(params (Rule, Parameter)[])`, `UpsertDataList`,
`ThrowIfContainsErrors`, Validations.cs:32-50) exists to collect several field
errors into one exception carrying a per-field data dictionary. Collapsed here
to a plain `if condition: raise LeafException(message)` — the same collapse
Session Lifecycle's ConversationSessionServiceValidations and Review's
ReviewOrchestratorValidations already made. Ingestion has two input fields
rather than Review's one, so this file keeps the reference's aggregator layer
that Review had nothing to aggregate for; it still fails on the first bad
field instead of accumulating both.

`_validate_embeddings_match_chunks` has no reference analog: the reference's
Orchestration service never validates a value it computed itself mid-flow, only
its caller's inputs. It lives here anyway so all three IngestionValidationError
raise sites sit in one file, which is the point of the .Validations.cs split.
"""

from typing import Sequence

from rag.models.ingestion.exceptions import IngestionValidationError


class IngestionServiceValidations:
    """Mixin: raises the leaf validation exception when input is unusable.

    See ingestion_service_exceptions.py for how these get wrapped and logged
    before leaving the service.
    """

    def _validate_ingest_topic_input(self, topic: str, source_url: str) -> None:
        """Mirrors ValidateEntitlementCodeInputOnRedeem, Validations.cs:12-17."""
        self._validate_topic(topic)
        self._validate_source_url(source_url)

    def _validate_topic(self, topic: str) -> None:
        """Mirrors the `IsInvalid(string text)` overload, Validations.cs:26-30."""
        if not topic or not topic.strip():
            raise IngestionValidationError("topic is required")

    def _validate_source_url(self, source_url: str) -> None:
        """Mirrors the `IsInvalid(string text)` overload, Validations.cs:26-30."""
        if not source_url or not source_url.strip():
            raise IngestionValidationError("source_url is required")

    def _validate_embeddings_match_chunks(
        self, embeddings: Sequence[Sequence[float]], chunks: Sequence[str]
    ) -> None:
        """No reference analog — see this module's docstring."""
        if len(embeddings) != len(chunks):
            raise IngestionValidationError(
                f"embedding count {len(embeddings)} does not match chunk count {len(chunks)}"
            )
