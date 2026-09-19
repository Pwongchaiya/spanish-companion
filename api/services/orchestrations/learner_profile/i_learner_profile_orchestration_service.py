"""Interface for the learner-profile-memory orchestration service.

typing.Protocol, not abc.ABC -- this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers), extended to service
interfaces the same way i_review_service.py does.

Naming: the file carries the `_orchestration_service` suffix (matching the
generic orchestration-service-skill's naming convention) rather than Review's
bare `i_review_service.py` shape, because "learner_profile" -- unlike
"review" -- is already a Foundation and Processing entity name in this
codebase (learner_profile_service.py exists at both those tiers). The suffix
is Processing's own disambiguation trick
(learner_profile_processing_service.py), reused here one tier up. Following
Review's Protocol-drops-the-suffix precedent to the letter would collide the
Protocol name (`LearnerProfileOrchestrationService`) with this file's own
concrete class, so the Protocol is named for what it does --
`LearnerProfileScenarioService` -- the same naming move Review made
(`ReviewService`, not `ReviewOrchestrationService`) and Session Lifecycle
made (`SessionLifecycleService`, not `ConversationSessionService`).
"""

from typing import Protocol

from api.models.orchestrations.learner_profile.session_scenario import SessionScenario


class LearnerProfileScenarioService(Protocol):
    """External-facing contract for the learner-profile-memory orchestration
    service."""

    def suggest_session_scenario(self) -> SessionScenario:
        """The next Conversation Mode session's opening scenario.

        Combines the singleton LearnerProfile (get-or-created via
        LearnerProfileProcessingService.ensure_profile()), the learner's
        MistakePattern rows, their TopicCovered rows, and recent Flag
        history into one SessionScenario:

        - proficiency_level: the profile's level (creating it at a
          config-driven default if this is the first session ever).
        - focus_category: the highest-occurrence *active* MistakePattern
          category, or None if the learner has no unresolved recurring
          mistake.
        - suggested_topic: focus_category if set (practicing the recurring
          mistake takes priority); otherwise the TopicCovered row least
          recently practiced (due for review); otherwise None (nothing
          covered yet).
        - recent_mistake_categories: deduped Flag categories from the most
          recent flags (config-driven limit), newest first.
        - due_patterns: mistake patterns whose spaced-review is due
          (MistakePatternProcessingService.list_due), next_due_at-ascending,
          capped at DUE_BRIEF_LIMIT (default 3). Coexists with
          focus_category/suggested_topic (A3 priming brief).

        Raises LearnerProfileOrchestrationValidationException (wrapping
        LearnerProfileValidationException, MistakePatternValidationException,
        or TopicCoveredValidationException) if a dependency rejects an
        input.
        Raises LearnerProfileOrchestrationDependencyException (wrapping
        LearnerProfileDependencyException, MistakePatternDependencyException,
        or TopicCoveredDependencyException) if a dependency's underlying
        storage call fails.
        Raises LearnerProfileOrchestrationServiceException for anything
        else.
        """
        ...


__all__ = ["LearnerProfileScenarioService"]
