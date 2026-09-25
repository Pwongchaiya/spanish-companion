"""Orchestration service for pronunciation scoring (roadmap Phase 4).

Composes two Foundation services -- IPronunciationAssessmentService (Azure
scoring) and IPronunciationResultService (persistence) -- into one flow:
assess, then record. Two dependencies, so the Florance 2-3 rule holds without
the ORC-001 waiver; only logging_broker is held directly (cross-cutting).

Same file layout as ReviewOrchestrationService
(api/services/orchestrations/review/review_service.py:1-76): concrete class
inherits the Exceptions mixin and the Protocol by name, every public method's
body is a closure passed to `_try_catch`, no local try/except inside it.
"""

from datetime import datetime
from typing import Any, Callable

from api.brokers.logging import LoggingBroker
from api.models.foundations.pronunciation_assessment.pronunciation_assessment import PronunciationAssessment
from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult
from api.services.foundations.pronunciation_assessment import IPronunciationAssessmentService
from api.services.foundations.pronunciation_result import IPronunciationResultService
from api.services.orchestrations.pronunciation.i_pronunciation_service import PronunciationService
from api.services.orchestrations.pronunciation.pronunciation_service_exceptions import (
    PronunciationOrchestrationServiceExceptions,
)

LOCALE = "es-ES"


def _words_json(assessment: PronunciationAssessment) -> list[dict[str, Any]]:
    return [
        {
            "word": w.word,
            "accuracy": w.accuracy_score,
            "error_type": w.error_type,
            "phonemes": [{"phoneme": p.phoneme, "accuracy": p.accuracy_score} for p in w.phonemes],
        }
        for w in assessment.words
    ]


class PronunciationOrchestrationService(PronunciationOrchestrationServiceExceptions, PronunciationService):
    """Owns the assess-then-record pronunciation flow."""

    def __init__(
        self,
        assessment_service: IPronunciationAssessmentService,
        result_service: IPronunciationResultService,
        clock: Callable[[], datetime] = datetime.now,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._assessment_service = assessment_service
        self._result_service = result_service
        # Injected: CLAUDE.md's unit-test rule forbids live datetime.now().
        self._clock = clock
        self._logging_broker = logging_broker

    def assess_and_record(
        self, audio_wav: bytes, reference_text: str, is_word_drill: bool = False
    ) -> PronunciationResult:
        def action() -> PronunciationResult:
            assessment = self._assessment_service.assess_pronunciation(audio_wav, reference_text)
            stored = self._result_service.create_pronunciation_result(
                PronunciationResult(
                    id=None,
                    created_at=self._clock(),
                    reference_text=reference_text,
                    accuracy_score=assessment.accuracy_score,
                    fluency_score=assessment.fluency_score,
                    completeness_score=assessment.completeness_score,
                    pronunciation_score=assessment.pronunciation_score,
                    prosody_score=assessment.prosody_score,
                    words_json=_words_json(assessment),
                    locale=LOCALE,
                    is_word_drill=is_word_drill,
                )
            )
            self._logging_broker.log_info("recorded pronunciation attempt, overall=%s", stored.pronunciation_score)
            return stored

        return self._try_catch(action)
