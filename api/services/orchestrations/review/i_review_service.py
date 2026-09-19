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
`ReviewOrchestrationService`.
"""

from typing import List, Optional, Protocol

from api.models.foundations.flag import Flag
from api.models.orchestrations.review.practice_result import PracticeResult
from api.models.orchestrations.review.task_outcome import TaskOutcome
from rag.models.foundations.generation import Explanation


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

    def get_task_outcome(self) -> Optional[TaskOutcome]:
        """Roadmap D4: the latest completed session's task-scenario outcome.

        Returns None if there is no completed session, or its scenario is
        absent/has no success_condition. Otherwise returns a TaskOutcome; if
        the session was not yet judged, judges it now (Generation LLM judge
        over the transcript) and persists the result to session_log. `outcome`
        stays None if it couldn't be judged (no transcript, judge failure) --
        retried on the next call. Never called in live Conversation Mode.

        Failures beneath (session_log / transcript storage) surface as
        ReviewOrchestrationServiceException.
        """
        ...

    def record_practice(
        self, flag_id: str, attempt_text: str, roleplay_slug: Optional[str] = None
    ) -> PracticeResult:
        """Log the learner's practice attempt, then judge it against the
        flag's correction and update learner memory (LearnerProfile Phase 2).

        After recording the attempt, a broker call judges whether
        attempt_text correctly applies flag.corrected. A "mastered" verdict
        resolves the matching mistake_pattern row (a no-op, logged, if none
        exists for this category yet); a "still shaky" verdict records an
        occurrence, creating the row if this is the first one. The returned
        PracticeResult carries both the durable attempt and the verdict.

        `roleplay_slug` (LearnerProfile Phase 4, optional) names a known
        roleplay scenario (api/data/roleplay_scenarios.py) -- resolved to its
        setting text here and passed to the judge for richer context. An
        unrecognized slug is silently treated as no roleplay context.

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
