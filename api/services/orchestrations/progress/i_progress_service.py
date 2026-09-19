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

from typing import List, Optional, Protocol

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.models.orchestrations.progress.speaking_total import SpeakingTotal
from api.models.orchestrations.progress.topic_coverage_entry import TopicCoverageEntry
from api.models.orchestrations.progress.unflagged_streak import UnflaggedStreak


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

    def get_speaking_total(self) -> SpeakingTotal:
        """Total time spoken across every completed session, plus how many
        sessions that was (C1).

        Reads `session_log` rows and sums (ended_at - started_at). Rows with
        no `ended_at` -- still running, or killed before completion -- are
        skipped, as are rows whose `ended_at` precedes `started_at` (clock
        change mid-session). Returns SpeakingTotal(0.0, 0) when nothing
        qualifies. No profile is resolved: `session_log` is not per-profile.

        Raises ProgressOrchestrationValidationException (wrapping
        SessionLogEntryValidationException) if the dependency rejects an
        input.
        Raises ProgressOrchestrationDependencyException (wrapping
        SessionLogEntryDependencyException) if its storage call fails.
        Raises ProgressOrchestrationServiceException for anything else.
        """
        ...

    def get_longest_unflagged_streak(self) -> UnflaggedStreak:
        """Longest and current runs of consecutive zero-flag sessions (C3).

        Walks the same completed-only `session_log` rows as
        get_speaking_total(), in `started_at` order, counting runs where
        `flag_count == 0`. `current` is the trailing run, `longest` the
        best. Both are 0 when no session has completed.

        Raises the same three exception tiers as get_speaking_total().
        """
        ...

    def get_latest_completed_session(self) -> Optional[SessionLogEntry]:
        """The most recently started `session_log` row with `ended_at` set
        (roadmap C2 post-session recap), or None if no session has ever
        completed.

        Reads the same completed-only, `started_at`-ordered rows as
        get_speaking_total()/get_longest_unflagged_streak() and returns the
        last one -- no new query shape, just a different fold over the same
        list.

        Raises the same three exception tiers as get_speaking_total().
        """
        ...


__all__ = ["ProgressService"]
