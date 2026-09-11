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
    """External-facing contract for MistakePattern's Foundation service."""

    def list_by_profile(self, profile_id: int) -> list[MistakePattern]:
        """All mistake-pattern rows for the given profile.

        Raises MistakePatternValidationException (wrapping
        InvalidMistakePatternInputError) if profile_id is not a positive int.
        Raises MistakePatternDependencyException (wrapping
        MistakePatternUnavailableError) if the underlying broker call fails.
        Raises MistakePatternServiceException for any other unexpected
        failure.
        """
        ...

    def create(self, profile_id: int, category: str) -> MistakePattern:
        """Insert a new mistake-pattern row.

        Raises MistakePatternValidationException (wrapping
        InvalidMistakePatternInputError) if profile_id is not a positive int
        or category is None/blank.
        Raises MistakePatternDependencyException (wrapping
        MistakePatternUnavailableError) if the underlying broker call fails
        (including a duplicate (profile_id, category) pair).
        Raises MistakePatternServiceException for any other unexpected
        failure.
        """
        ...

    def update(self, pattern_id: int, occurrence_count: int, status: str) -> MistakePattern:
        """Update the given row's occurrence_count and status.

        Raises MistakePatternValidationException (wrapping
        InvalidMistakePatternInputError) if pattern_id is not a positive
        int, occurrence_count < 1, or status is not "active"/"resolved".
        Raises MistakePatternDependencyException (wrapping
        MistakePatternUnavailableError) if the underlying broker call fails
        (including pattern_id not existing).
        Raises MistakePatternServiceException for any other unexpected
        failure.
        """
        ...
