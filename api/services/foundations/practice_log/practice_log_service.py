"""Foundation service wrapping PracticeLogBroker.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers -- same shape as
ConversationSessionService (api/services/session_lifecycle/).

Absorbs the blank-check validation that used to live in
ReviewOrchestratorValidations._validate_practice_input
(api/services/review/review_service_validations.py). That file and
review_service.py are untouched by this wave -- Wave 5 rewires
ReviewOrchestrationService to call this service instead.

No `_PracticeLogServiceBase` / composition step -- matches
LearnerProfileService's rebuilt shape: one class, declared once,
`class X(XExceptions, XValidations, IX):`, constructor and public methods
on it directly (the previous `_PracticeLogServiceBase` + __init__.py
composition step was the invented-`_ServiceBase` pattern CLAUDE.md
explicitly disallows -- removed).

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin): each public method's entire body -- validate, then
call the broker -- is an inline nested closure passed straight to
`_try_catch`, not a separate `_do_thing` private method with its own local
try/except.
"""

from typing import List, Optional

from api.brokers.logging import LoggingBroker
from api.brokers.practice_log import PracticeAttempt, PracticeLogBroker
from api.models.foundations.practice_log.exceptions import PracticeLogUnavailableError
from api.services.foundations.practice_log.i_practice_log_service import IPracticeLogService
from api.services.foundations.practice_log.practice_log_service_exceptions import (
    PracticeLogServiceExceptions,
)
from api.services.foundations.practice_log.practice_log_service_validations import (
    PracticeLogServiceValidations,
)


class PracticeLogService(
    PracticeLogServiceExceptions,
    PracticeLogServiceValidations,
    IPracticeLogService,
):
    """Owns PracticeAttempt recording/reading. Validation checks are named
    methods (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        practice_log_broker: PracticeLogBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._practice_log_broker = practice_log_broker
        self._logging_broker = logging_broker

    def record_attempt(self, attempt: PracticeAttempt) -> None:
        def action() -> None:
            self._validate_attempt_text(attempt.attempt_text)
            try:
                self._practice_log_broker.record_attempt(attempt)
            except Exception as e:
                raise PracticeLogUnavailableError(str(e)) from e

        return self._try_catch(action)

    def read_attempts(self, flag_id: Optional[str] = None) -> List[PracticeAttempt]:
        def action() -> List[PracticeAttempt]:
            try:
                return self._practice_log_broker.read_attempts(flag_id)
            except Exception as e:
                raise PracticeLogUnavailableError(str(e)) from e

        return self._try_catch(action)
