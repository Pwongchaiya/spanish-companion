"""Foundation service for pronunciation assessment (Phase 4 B1).

Wraps PronunciationAssessmentBroker with input validation and exception mapping only -- single broker,
no higher-order logic. Same shape as TtsService (api/services/foundations/tts/tts_service.py): the whole
public-method body is a closure passed to `_try_catch`, with one narrow catch turning a raw broker failure
into the leaf PronunciationAssessmentUnavailableError.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.pronunciation_assessment.i_pronunciation_assessment_broker import PronunciationAssessmentBroker
from api.models.foundations.pronunciation_assessment.exceptions import PronunciationAssessmentUnavailableError
from api.models.foundations.pronunciation_assessment.pronunciation_assessment import PronunciationAssessment
from api.services.foundations.pronunciation_assessment.i_pronunciation_assessment_service import (
    IPronunciationAssessmentService,
)
from api.services.foundations.pronunciation_assessment.pronunciation_assessment_service_exceptions import (
    PronunciationAssessmentServiceExceptions,
)
from api.services.foundations.pronunciation_assessment.pronunciation_assessment_service_validations import (
    PronunciationAssessmentServiceValidations,
)


class PronunciationAssessmentService(
    PronunciationAssessmentServiceExceptions,
    PronunciationAssessmentServiceValidations,
    IPronunciationAssessmentService,
):
    """Owns WAV + reference text -> PronunciationAssessment scoring."""

    def __init__(
        self,
        pronunciation_assessment_broker: PronunciationAssessmentBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._pronunciation_assessment_broker = pronunciation_assessment_broker
        self._logging_broker = logging_broker

    def assess_pronunciation(self, wav_bytes: bytes, reference_text: str) -> PronunciationAssessment:
        def action() -> PronunciationAssessment:
            self._validate_on_assess_pronunciation(wav_bytes, reference_text)
            try:
                return self._pronunciation_assessment_broker.assess(wav_bytes, reference_text)
            except Exception as e:
                raise PronunciationAssessmentUnavailableError(str(e)) from e

        return self._try_catch(action)
