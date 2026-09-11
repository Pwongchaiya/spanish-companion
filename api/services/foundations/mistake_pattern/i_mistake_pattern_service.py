"""Interface for the mistake-pattern Foundation service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as ILearnerProfileService.

Pure CRUD only -- no upsert, no find-by-category. record_occurrence() /
resolve() are Processing-tier logic, built later against this interface
(see Projects/spanish-companion/entities/mistake-pattern.md).
"""

from typing import Protocol

from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern


class IMistakePatternService(Protocol):
    """External-facing contract for MistakePattern's Foundation service.

    Method names embed the entity name, matching NL.Core.Users' Service
    interface methods (`AddUserProfileAsync`, `ModifyUserProfileAsync`,
    `RetrieveUserProfileByIdAsync` -- IUserProfileService.cs) -- verbs stay
    this project's own create/update/list (a project-wide REST/CRUD
    adaptation of Add/Modify/Retrieve), but the entity name is no longer
    dropped.
    """

    def list_mistake_patterns_by_profile(self, profile_id: int) -> list[MistakePattern]:
        """All mistake-pattern rows for the given profile.

        Raises MistakePatternValidationException (wrapping
        InvalidMistakePatternException) if profile_id is not a positive int.
        Raises MistakePatternDependencyException (wrapping
        FailedMistakePatternStorageException) if the underlying broker call fails.
        Raises MistakePatternServiceException for any other unexpected
        failure.
        """
        ...

    def create_mistake_pattern(self, profile_id: int, category: str) -> MistakePattern:
        """Insert a new mistake-pattern row.

        Raises MistakePatternValidationException (wrapping
        InvalidMistakePatternException) if profile_id is not a positive int
        or category is None/blank.
        Raises MistakePatternDependencyException (wrapping
        FailedMistakePatternStorageException) if the underlying broker call fails
        (including a duplicate (profile_id, category) pair).
        Raises MistakePatternServiceException for any other unexpected
        failure.
        """
        ...

    def update_mistake_pattern(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        """Update the given row's occurrence_count and status.

        Raises MistakePatternValidationException (wrapping
        InvalidMistakePatternException) if pattern_id is not a positive
        int, occurrence_count < 1, or status is not "active"/"resolved".
        Raises MistakePatternDependencyException (wrapping
        FailedMistakePatternStorageException) if the underlying broker call fails
        (including pattern_id not existing).
        Raises MistakePatternServiceException for any other unexpected
        failure.
        """
        ...
