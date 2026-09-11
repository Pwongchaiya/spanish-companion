"""Interface for the learner-profile Foundation service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as IFlagService /
ISessionLifecycleService: the reference project co-locates the interface
file with its implementation.

Pure CRUD only -- no upsert, no get-or-create. ensure_profile() is
Processing-tier logic, built later against this interface (see
Projects/spanish-companion/entities/learner-profile.md).
"""

from typing import Protocol

from api.models.foundations.learner_profile.learner_profile import LearnerProfile


class ILearnerProfileService(Protocol):
    """External-facing contract for LearnerProfile's Foundation service."""

    def create_profile(self, proficiency_level: str) -> LearnerProfile:
        """Insert a new profile row.

        Raises LearnerProfileValidationException (wrapping
        InvalidLearnerProfileInputError) if proficiency_level is None or
        blank.
        Raises LearnerProfileDependencyException (wrapping
        LearnerProfileUnavailableError) if the underlying broker call fails.
        Raises LearnerProfileServiceException for any other unexpected
        failure.
        """
        ...

    def get_profile(self) -> LearnerProfile:
        """The one profile row.

        Raises LearnerProfileValidationException (wrapping
        NotFoundLearnerProfileException) if no profile row exists yet --
        this service does not create one; that's Processing's ensure_profile().
        Raises LearnerProfileDependencyException (wrapping
        LearnerProfileUnavailableError) if the underlying broker call fails.
        Raises LearnerProfileServiceException for any other unexpected
        failure.
        """
        ...

    def update_proficiency_level(self, profile_id: int, proficiency_level: str) -> LearnerProfile:
        """Update the given profile row's proficiency_level.

        Raises LearnerProfileValidationException (wrapping
        InvalidLearnerProfileInputError) if proficiency_level is None or
        blank.
        Raises LearnerProfileDependencyException (wrapping
        LearnerProfileUnavailableError) if the underlying broker call fails
        (including profile_id not existing).
        Raises LearnerProfileServiceException for any other unexpected
        failure.
        """
        ...
