"""Interface for the Pronunciation orchestration service (roadmap Phase 4).

typing.Protocol, not abc.ABC, per this project's interface waiver, co-located
with the implementation like api/services/orchestrations/review/i_review_service.py.
"""

from typing import Protocol

from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult


class PronunciationService(Protocol):
    """External-facing contract for the Pronunciation orchestration service."""

    def assess_and_record(self, audio_wav: bytes, reference_text: str) -> PronunciationResult:
        """Score a spoken WAV against reference_text, persist the attempt, return the stored row.

        Raises PronunciationOrchestrationValidationException (wrapping
        PronunciationAssessmentValidationException) if the audio/text is rejected.
        Raises PronunciationOrchestrationDependencyException (wrapping
        PronunciationAssessmentDependencyException, or
        PronunciationResultDependencyException when persisting fails after a
        successful assessment -- never swallowed).
        Raises PronunciationOrchestrationServiceException for anything else.
        """
        ...


__all__ = ["PronunciationService"]
