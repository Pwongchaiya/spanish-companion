"""Foundation service for the pronunciation_result entity (Phase 4 B5).

Wraps IPronunciationResultBroker (api/brokers/pronunciation_result/) with
input validation only -- pure CRUD, no trend logic. Single broker dependency
-> Foundation layer. Split into logic + Validations/Exceptions mixins, the
concrete class declared here, mirroring
api/services/foundations/session_log_entry/session_log_entry_service.py.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.pronunciation_result.i_pronunciation_result_broker import IPronunciationResultBroker
from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult
from api.services.foundations.pronunciation_result.i_pronunciation_result_service import IPronunciationResultService
from api.services.foundations.pronunciation_result.pronunciation_result_service_exceptions import (
    PronunciationResultServiceExceptions,
)
from api.services.foundations.pronunciation_result.pronunciation_result_service_validations import (
    PronunciationResultServiceValidations,
)


class PronunciationResultService(
    PronunciationResultServiceExceptions,
    PronunciationResultServiceValidations,
    IPronunciationResultService,
):
    """Owns PronunciationResult CRUD."""

    def __init__(
        self,
        pronunciation_result_broker: IPronunciationResultBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._pronunciation_result_broker = pronunciation_result_broker
        self._logging_broker = logging_broker

    def create_pronunciation_result(self, result: PronunciationResult) -> PronunciationResult:
        def action() -> PronunciationResult:
            self._validate_pronunciation_result_on_create(result)
            return self._pronunciation_result_broker.insert_pronunciation_result(result)

        return self._try_catch(action)

    def list_pronunciation_results(self) -> list[PronunciationResult]:
        def action() -> list[PronunciationResult]:
            return self._pronunciation_result_broker.select_all_pronunciation_results()

        return self._try_catch(action)
