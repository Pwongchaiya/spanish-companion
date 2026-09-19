"""Broker for Azure Pronunciation Assessment (Phase 4 B1).

typing.Protocol, not ABC, per this project's broker-interface waiver (CLAUDE.md), co-located with its
implementation, same as TtsBroker (api/brokers/tts/i_tts_broker.py).
"""

from typing import Protocol

from api.models.foundations.pronunciation_assessment.pronunciation_assessment import PronunciationAssessment


class PronunciationAssessmentBroker(Protocol):
    """External-resource boundary for scoring one spoken utterance against reference text.
    No business logic, no input validation."""

    def assess(self, wav_bytes: bytes, reference_text: str) -> PronunciationAssessment:
        """Score the WAV (16 kHz mono 16-bit PCM) against reference_text.

        Raises whatever the SDK/transport raises on failure (RuntimeError on no-match, cancellation or
        timeout) -- PronunciationAssessmentService wraps it into PronunciationAssessmentUnavailableError,
        mirroring TtsBroker.
        """
        ...
