"""Validation checks for ReviewOrchestrator.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
EntitlementCodesOrchestrationService.Validations.cs:12-51 -- a named
`Validate<Thing>Input...` method called from the main service file's method
bodies rather than inlined there.

Cited divergence: the reference's rule/accumulator machinery
(`Validate(params (Rule, Parameter)[])`, `UpsertDataList`,
`ThrowIfContainsErrors`, Validations.cs:20-50) exists to collect several
field errors into one exception. Review validates exactly one field, so
that machinery is collapsed to a single `if (condition): raise
LeafException()` -- the same shape Session Lifecycle's
ConversationSessionServiceValidations already uses.

This check moved here from api/controllers/review.py, where it previously
lived inline as a 400 before the service was called.
"""

from api.models.review.exceptions import InvalidReviewOrchestrationException


class ReviewOrchestratorValidations:
    """Mixin: raises the leaf validation exception when caller input is
    unusable. See review_service_exceptions.py for how these get wrapped
    and logged before leaving the service.
    """

    def _validate_practice_input(self, attempt_text: str) -> None:
        if not isinstance(attempt_text, str) or not attempt_text.strip():
            raise InvalidReviewOrchestrationException()
