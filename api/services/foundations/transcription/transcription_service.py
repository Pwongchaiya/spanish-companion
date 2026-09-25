"""Foundation service for transcription (Section 4, review-three-pane HANDOFF.md).

Wraps TranscriptionBroker with input validation and exception mapping only -- single broker, no
higher-order logic. Same shape as PronunciationAssessmentService
(api/services/foundations/pronunciation_assessment/pronunciation_assessment_service.py): the whole
public-method body is a closure passed to `_try_catch`, with one narrow catch turning a raw broker
failure into the leaf TranscriptionUnavailableError.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.transcription.i_transcription_broker import TranscriptionBroker
from api.models.foundations.transcription.exceptions import TranscriptionUnavailableError
from api.models.foundations.transcription.transcription import Transcription
from api.services.foundations.transcription.i_transcription_service import ITranscriptionService
from api.services.foundations.transcription.transcription_service_exceptions import TranscriptionServiceExceptions
from api.services.foundations.transcription.transcription_service_validations import TranscriptionServiceValidations


class TranscriptionService(
    TranscriptionServiceExceptions,
    TranscriptionServiceValidations,
    ITranscriptionService,
):
    """Owns WAV bytes -> Transcription (free-form, no reference text)."""

    def __init__(
        self,
        transcription_broker: TranscriptionBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._transcription_broker = transcription_broker
        self._logging_broker = logging_broker

    def transcribe(self, wav_bytes: bytes) -> Transcription:
        def action() -> Transcription:
            self._validate_on_transcribe(wav_bytes)
            try:
                return self._transcription_broker.transcribe(wav_bytes)
            except Exception as e:
                raise TranscriptionUnavailableError(str(e)) from e

        return self._try_catch(action)
