"""Interface for the Progress orchestration service (roadmap Phase 2: A5
cumulative mistake dashboard, F1 corpus coverage map).

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces the same way i_review_service.py does.

Naming follows Review's precedent exactly -- "progress" isn't already a
Foundation/Processing entity name in this codebase, so the Protocol is
`ProgressService` (feature name, no suffix) and the concrete class is
`ProgressOrchestrationService`.
"""

from typing import List, Protocol

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.orchestrations.progress.topic_coverage_entry import TopicCoverageEntry


class ProgressService(Protocol):
    """External-facing contract for the Progress orchestration service."""

    def list_mistake_summary(self) -> List[MistakePattern]:
        """Every MistakePattern row for the singleton profile (A5).

        Get-or-creates the singleton profile first (same
        LearnerProfileProcessingService.ensure_profile() call every other
        Progress/LearnerProfile-consuming feature makes), then reads its
        mistake-pattern rows as-is -- no filtering, no sorting; the caller
        (Exposer/frontend) decides how to present a cumulative dashboard.

        Raises ProgressOrchestrationValidationException (wrapping
        LearnerProfileValidationException or MistakePatternValidationException)
        if a dependency rejects an input.
        Raises ProgressOrchestrationDependencyException (wrapping
        LearnerProfileDependencyException or MistakePatternDependencyException)
        if a dependency's underlying storage call fails.
        Raises ProgressOrchestrationServiceException for anything else.
        """
        ...

    def list_topic_coverage(self) -> List[TopicCoverageEntry]:
        """The full corpus topic list (rag/data/topics.py), each entry
        marked covered/not-covered against the singleton profile's
        TopicCovered rows (F1).

        Get-or-creates the singleton profile first, reads its TopicCovered
        rows, then walks the corpus's distinct topic names (order
        preserved, duplicates from the (topic, url) pairs in
        rag/data/topics.py collapsed) building one TopicCoverageEntry per
        topic -- covered=True with first_covered_at set if a TopicCovered
        row exists for it, else covered=False with first_covered_at=None.

        Raises ProgressOrchestrationValidationException (wrapping
        LearnerProfileValidationException or TopicCoveredValidationException)
        if a dependency rejects an input.
        Raises ProgressOrchestrationDependencyException (wrapping
        LearnerProfileDependencyException or TopicCoveredDependencyException)
        if a dependency's underlying storage call fails.
        Raises ProgressOrchestrationServiceException for anything else.
        """
        ...


__all__ = ["ProgressService"]
