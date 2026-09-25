"""Broker for free-form Azure transcription (Section 4, review-three-pane HANDOFF.md).

typing.Protocol, not ABC, per this project's broker-interface waiver (CLAUDE.md), co-located with its
implementation, same as PronunciationAssessmentBroker
(api/brokers/pronunciation_assessment/i_pronunciation_assessment_broker.py).
"""

from typing import Protocol

from api.models.foundations.transcription.transcription import Transcription


class TranscriptionBroker(Protocol):
    """External-resource boundary for recognising one WAV utterance with no reference text
    (unbiased recognition). No business logic, no input validation."""

    def transcribe(self, wav_bytes: bytes) -> Transcription:
        """Recognise the WAV (16 kHz mono 16-bit PCM).

        `ResultReason.NoMatch` returns `Transcription(text="", ...)`, not an exception. Raises whatever
        the SDK/transport raises on a real failure (RuntimeError on cancellation or timeout) --
        TranscriptionService wraps it into TranscriptionUnavailableError, mirroring
        PronunciationAssessmentBroker.
        """
        ...
