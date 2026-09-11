"""Interface for the learner-profile Foundation service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as IMistakePatternService: the
reference project co-locates the interface file with its implementation.

Pure CRUD only -- no upsert, no get-or-create. ensure_profile() is
Processing-tier logic, built later against this interface (see
Projects/spanish-companion/entities/learner-profile.md).

Method names embed the entity name, matching NL.Core.Users' Service
interface methods (AddUserProfileAsync, ModifyUserProfileAsync,
RetrieveUserProfileByIdAsync -- IUserProfileService.cs) -- verbs stay this
project's own create/get/update, but the entity name is no longer dropped
(same convention already applied to IMistakePatternService).
"""

from typing import Protocol

from api.models.foundations.learner_profile.learner_profile import LearnerProfile


class ILearnerProfileService(Protocol):
    """External-facing contract for LearnerProfile's Foundation service."""

    def create_learner_profile(self, proficiency_level: str) -> LearnerProfile:
        """Insert a new profile row.

        Raises LearnerProfileValidationException (wrapping
        InvalidLearnerProfileException) if proficiency_level is None or
        blank.
        Raises LearnerProfileDependencyException (wrapping
        FailedLearnerProfileStorageException) if the underlying broker call
        fails.
        Raises LearnerProfileServiceException for any other unexpected
        failure.
        """
        ...

    def get_learner_profile(self) -> LearnerProfile:
        """The one profile row.

        Raises LearnerProfileValidationException (wrapping
        NotFoundLearnerProfileException) if no profile row exists yet --
        this service does not create one; that's Processing's ensure_profile().
        Raises LearnerProfileDependencyException (wrapping
        FailedLearnerProfileStorageException) if the underlying broker call
        fails.
        Raises LearnerProfileServiceException for any other unexpected
        failure.
        """
        ...

    def update_learner_profile(self, profile_id: int, proficiency_level: str) -> LearnerProfile:
        """Update the given profile row's proficiency_level.

        Raises LearnerProfileValidationException (wrapping
        InvalidLearnerProfileException if profile_id/proficiency_level fail
        input checks, or NotFoundLearnerProfileException if profile_id
        doesn't exist).
        Raises LearnerProfileDependencyException (wrapping
        FailedLearnerProfileStorageException) if the underlying broker call
        fails.
        Raises LearnerProfileServiceException for any other unexpected
        failure.
        """
        ...
