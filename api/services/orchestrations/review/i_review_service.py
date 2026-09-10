"""Interface for the Review Mode orchestration service.

Mirrors NL.Core.Entitlements.Api/Services/Orchestrations/EntitlementCodes/
IEntitlementCodesOrchestrationService.cs:10-13 -- typing.Protocol, not
abc.ABC, per this project's broker-interface waiver (CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers table), extended to service interfaces the
same way api/services/session_lifecycle/i_session_lifecycle_service.py
does: the reference project itself co-locates the interface file with its
implementation in the same folder.

Naming follows the Session Lifecycle precedent exactly -- there the
Protocol is `SessionLifecycleService` (feature name) and the concrete
class is `ConversationSessionService`. Here the Protocol is
`ReviewService` (feature name) and the concrete class stays
`ReviewOrchestrator`.
"""

from typing import List, Protocol

from api.brokers.practice_log import PracticeAttempt
from api.models.flag import Flag
from rag.models.generation import Explanation


class ReviewService(Protocol):
    """External-facing contract for Review Mode's orchestration service."""

    def list_flags(self) -> List[Flag]:
        """The current flag list, for the flagged-list -> selection step.

        Returns [] for a missing or corrupt flag file -- "no flags yet" is a
        normal state, not an error. Raises ReviewOrchestrationServiceException
        for any genuine broker failure behind it (an unreadable file, a
        permission error); it does not raise a validation exception, having no
        input to validate.
        """
        ...

    def explain_flag(self, flag_id: str) -> Explanation:
        """Grounded explanation of one flag, chosen by id.

        Raises ReviewOrchestrationValidationException (wrapping
        FlagValidationException, which itself holds NotFoundFlagException) if
        no flag has this id, ReviewOrchestrationDependencyException (wrapping
        RetrievalOrchestrationDependencyException, which itself holds
        RetrievalUnavailableError) if retrieval is unreachable, or
        ReviewOrchestrationServiceException for anything else.

        Also raises ReviewOrchestrationValidationException wrapping
        RetrievalOrchestrationValidationException if the flag's corrected text
        is unusable as a retrieval query.
        """
        ...

    def record_practice(self, flag_id: str, attempt_text: str) -> PracticeAttempt:
        """Log the learner's single practice attempt at a flag's correction.

        Raises ReviewOrchestrationValidationException wrapping either
        FlagValidationException (unknown flag_id, holding
        NotFoundFlagException) or PracticeLogValidationException (blank
        attempt_text, holding InvalidPracticeAttemptException), or
        ReviewOrchestrationServiceException for anything else.

        The flag lookup runs first, so an unknown flag_id is reported even
        when attempt_text is also blank.
        """
        ...


__all__ = ["ReviewService"]
