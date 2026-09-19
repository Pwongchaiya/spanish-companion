"""Interface for the pronunciation-result Foundation service (Phase 4 B5).

typing.Protocol, not abc.ABC, per this project's interface waiver (CLAUDE.md).
Pure CRUD only -- trend/average logic belongs to a higher tier.
Mirrors api/services/foundations/session_log_entry/i_session_log_entry_service.py.
"""

from typing import Protocol

from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult


class IPronunciationResultService(Protocol):
    """External-facing contract for PronunciationResult's Foundation service."""

    def create_pronunciation_result(self, result: PronunciationResult) -> PronunciationResult:
        """Insert a scored pronunciation attempt.

        Raises PronunciationResultValidationException (wrapping
        InvalidPronunciationResultException) if result is None or any field
        fails validation.
        Raises PronunciationResultDependencyException (wrapping
        FailedPronunciationResultStorageException) if the broker call fails.
        Raises PronunciationResultServiceException for any other unexpected
        failure.
        """
        ...

    def list_pronunciation_results(self) -> list[PronunciationResult]:
        """Every stored result, oldest first.

        Raises PronunciationResultDependencyException (wrapping
        FailedPronunciationResultStorageException) if the broker call fails.
        Raises PronunciationResultServiceException for any other unexpected
        failure.
        """
        ...
