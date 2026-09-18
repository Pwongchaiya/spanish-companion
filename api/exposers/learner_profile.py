"""In-process (non-HTTP) exposer for the LearnerProfile scenario-suggestion
feature.

Not a Flask Blueprint -- called directly by future Voice Conversation
(session start) and Review (session-close summary) call sites per
learner-profile.md's Exposer row, matching the shape the codebase's earlier
in-process controllers (rag/controllers/generation.py's GenerationController,
rag/controllers/retrieval.py's RetrievalController) used before they were
deleted for having a single caller each -- LearnerProfile keeps its
controller because it has two eventual callers, not one, so a shared entry
point still earns its keep.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers: versioning and
HTTP status-code mapping are both waived here, same as the deleted
controllers, since there is no HTTP response to map. What HTTP-facing
Exposers still owe -- an explicit `except` per exception category, never a
catch-all `except Exception` -- is kept: each of LearnerProfileScenarioService's
three public wrapper exceptions (Validation/Dependency/ServiceException;
FailedLearnerProfileOrchestrationServiceException never reaches a caller
directly, same as Review's controller only importing three of Review's four)
gets its own clause. With no status code to assign, chained re-raise
(`raise` inside the same `except`, preserving the original traceback) is the
entire mapping -- this documents the exception surface for whichever caller
lands first (Voice Conversation or Review) without inventing behaviour
neither has asked for yet.
"""

from api.models.orchestrations.learner_profile.exceptions import (
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)
from api.models.orchestrations.learner_profile.session_scenario import SessionScenario
from api.services.orchestrations.learner_profile.i_learner_profile_orchestration_service import (
    LearnerProfileScenarioService,
)


class LearnerProfileController:
    """Public entry point for the LearnerProfile scenario suggestion.
    No logic beyond delegation and exception documentation."""

    def __init__(self, service: LearnerProfileScenarioService) -> None:
        self._service = service

    def suggest_session_scenario(self) -> SessionScenario:
        try:
            return self._service.suggest_session_scenario()
        except LearnerProfileOrchestrationValidationException:
            raise
        except LearnerProfileOrchestrationDependencyException:
            raise
        except LearnerProfileOrchestrationServiceException:
            raise
