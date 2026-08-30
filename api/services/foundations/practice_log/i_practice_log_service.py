"""Interface for the practice-attempt log Foundation service.

typing.Protocol, not abc.ABC, per CLAUDE.md's Phase 2 Layer-Agent Mapping &
Waivers (broker interfaces) extended to service interfaces -- same
reasoning and shape as api.services.session_lifecycle.i_session_lifecycle_service.
"""

from typing import List, Optional, Protocol

from api.brokers.practice_log import PracticeAttempt


class IPracticeLogService(Protocol):
    """External-facing contract for Practice Log's Foundation service."""

    def record_attempt(self, attempt: PracticeAttempt) -> None:
        """Persist one practice attempt.

        Raises PracticeLogValidationException (wrapping
        InvalidPracticeAttemptException) if attempt.attempt_text is blank.
        Raises PracticeLogDependencyException (wrapping
        PracticeLogUnavailableError) if the broker call fails.
        Raises PracticeLogServiceException for any other unexpected error.
        """
        ...

    def read_attempts(self, flag_id: Optional[str] = None) -> List[PracticeAttempt]:
        """Return all attempts, or only the ones matching flag_id if given.

        Raises PracticeLogDependencyException (wrapping
        PracticeLogUnavailableError) if the broker call fails.
        Raises PracticeLogServiceException for any other unexpected error.
        """
        ...
