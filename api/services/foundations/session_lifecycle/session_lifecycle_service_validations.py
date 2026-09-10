"""Validation checks for ConversationSessionService.

Mirrors NL.Core.Entitlements.Api/Services/Foundations/Entitlements/
EntitlementService.Validations.cs:73-82 (ValidateStorageEntitlementExists) --
a private method containing a single `if (condition): raise LeafException()`
check, called from the main service file's public-method bodies rather than
inlined there.
"""

from api.models.foundations.session_lifecycle.exceptions import (
    AlreadyRunningSessionException,
    NotRunningSessionException,
)


class ConversationSessionServiceValidations:
    """Mixin: raises the leaf exceptions when broker state doesn't match
    what the caller expects. See session_lifecycle_service_exceptions.py
    for how these get wrapped and logged before leaving the service.
    """

    def _validate_not_already_running(self) -> None:
        if self._broker.is_running():
            raise AlreadyRunningSessionException()

    def _validate_currently_running(self) -> None:
        if not self._broker.is_running():
            raise NotRunningSessionException()
