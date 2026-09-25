"""Foundation service for text-to-speech synthesis (roadmap item B6:
minimal-pair listening check).

Wraps TtsBroker (api/brokers/tts/) with input validation only -- no
Orchestration layer, no Processing layer: this is a stateless single-call
feature (validate text, delegate to the broker, return bytes), matching
this project's own precedent of deleting single-caller pass-through layers
(CLAUDE.md's Exposer waiver note on RetrievalController/GenerationController).

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers.

One class, declared once here -- mirrors FlagService/TopicCoveredService's
shape (no separate `_ServiceBase` + __init__.py composition step).

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): synthesize_speech()'s entire body -- validate, then
call the broker -- is an inline nested closure passed straight to
`_try_catch`. No local try/except beyond the one narrow catch needed to
turn a raw broker failure into the leaf TtsUnavailableError, mirroring
FlagService.save_flags()'s identical shape.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.tts.i_tts_broker import TtsBroker
from api.models.foundations.tts.exceptions import TtsUnavailableError
from api.services.foundations.tts.i_tts_service import ITtsService
from api.services.foundations.tts.tts_service_exceptions import TtsServiceExceptions
from api.services.foundations.tts.tts_service_validations import TtsServiceValidations


class TtsService(TtsServiceExceptions, TtsServiceValidations, ITtsService):
    """Owns Spanish text -> WAV bytes synthesis."""

    def __init__(
        self,
        tts_broker: TtsBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._tts_broker = tts_broker
        self._logging_broker = logging_broker

    def synthesize_speech(self, text: str, rate: float = 1.0) -> bytes:
        def action() -> bytes:
            self._validate_tts_on_synthesize(text, rate)
            try:
                return self._tts_broker.synthesize(text, rate)
            except Exception as e:
                raise TtsUnavailableError(str(e)) from e

        return self._try_catch(action)
