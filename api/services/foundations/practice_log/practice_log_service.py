"""Foundation service wrapping PracticeLogBroker.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers -- same shape as
ConversationSessionService (api/services/session_lifecycle/).

Absorbs the blank-check validation that used to live in
ReviewOrchestratorValidations._validate_practice_input
(api/services/review/review_service_validations.py). That file and
review_service.py are untouched by this wave -- Wave 5 rewires
ReviewOrchestrator to call this service instead.

Split into a base logic file plus Validations/Exceptions mixins (this file,
practice_log_service_validations.py, practice_log_service_exceptions.py),
combined into the concrete PracticeLogService in __init__.py -- mirrors
C#'s `partial class` merging multiple files into one class
(python-adaptations-skill.md's Architecture Patterns table), same pattern
as ConversationSessionService.
"""

from typing import List, Optional

from api.brokers.logging import LoggingBroker, StdlibLoggingBroker
from api.brokers.practice_log import PracticeAttempt, PracticeLogBroker
from api.models.practice_log.exceptions import PracticeLogUnavailableError


class _PracticeLogServiceBase:
    """Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per python-adaptations-
    skill.md's TryCatch translation. Validation checks are named methods
    (defined in the Validations mixin) rather than inlined.
    """

    def __init__(
        self,
        practice_log_broker: PracticeLogBroker,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._practice_log_broker = practice_log_broker
        self._logging_broker = logging_broker

    def record_attempt(self, attempt: PracticeAttempt) -> None:
        self._try_catch(lambda: self._record_attempt(attempt))

    def _record_attempt(self, attempt: PracticeAttempt) -> None:
        self._validate_attempt_text(attempt.attempt_text)
        try:
            self._practice_log_broker.record_attempt(attempt)
        except Exception as e:
            raise PracticeLogUnavailableError(str(e)) from e

    def read_attempts(self, flag_id: Optional[str] = None) -> List[PracticeAttempt]:
        return self._try_catch(lambda: self._read_attempts(flag_id))

    def _read_attempts(self, flag_id: Optional[str]) -> List[PracticeAttempt]:
        try:
            return self._practice_log_broker.read_attempts(flag_id)
        except Exception as e:
            raise PracticeLogUnavailableError(str(e)) from e
