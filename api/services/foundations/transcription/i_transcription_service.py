"""Interface for the transcription Foundation service.

typing.Protocol, not abc.ABC, per this project's waiver (CLAUDE.md), same as IPronunciationAssessmentService.
"""

from typing import Protocol

from api.models.foundations.transcription.transcription import Transcription


class ITranscriptionService(Protocol):
    """External-facing contract for the transcription Foundation service."""

    def transcribe(self, wav_bytes: bytes) -> Transcription:
        """Recognise one WAV utterance with no reference text (unbiased recognition).

        Raises TranscriptionValidationException (wrapping InvalidTranscriptionRequestException)
        if the WAV is missing/empty/header-only or not RIFF-WAVE.
        Raises TranscriptionDependencyException (wrapping TranscriptionUnavailableError)
        if the broker call fails.
        Raises TranscriptionServiceException for any other unexpected failure.

        `ResultReason.NoMatch` is NOT an error -- it returns Transcription(text="", ...).
        """
        ...
