"""Interface for the pronunciation assessment Foundation service.

typing.Protocol, not abc.ABC, per this project's waiver (CLAUDE.md), same as ITtsService.
"""

from typing import Protocol

from api.models.foundations.pronunciation_assessment.pronunciation_assessment import PronunciationAssessment


class IPronunciationAssessmentService(Protocol):
    """External-facing contract for the pronunciation assessment Foundation service."""

    def assess_pronunciation(self, wav_bytes: bytes, reference_text: str) -> PronunciationAssessment:
        """Score a spoken WAV against reference_text.

        Raises PronunciationAssessmentValidationException (wrapping InvalidPronunciationAssessmentRequestException)
        if the WAV is empty/oversized/not RIFF-WAVE or the reference text is blank/too long.
        Raises PronunciationAssessmentDependencyException (wrapping PronunciationAssessmentUnavailableError)
        if the broker call fails.
        Raises PronunciationAssessmentServiceException for any other unexpected failure.
        """
        ...
