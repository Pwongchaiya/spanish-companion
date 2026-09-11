"""Foundation service for the end-of-session review log.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Formatting logic
(save_session_log's body) moved here verbatim from
api/services/orchestrations/voice_conversation/voice_conversation_service.py
-- the Orchestrator still owns flattening LLMContext into `turns` (a
pipecat-specific concern this Foundation shouldn't need to know about), and
passes already-flattened strings in.

No composition step in __init__.py -- the concrete class is declared
directly in this file, inheriting the Exceptions mixin by name. Mirrors
LearnerProfileService's rebuilt shape (learner_profile_service.py): the
previous `_SessionLogServiceBase` + __init__.py composition class was the
invented-`_ServiceBase` pattern CLAUDE.md explicitly disallows -- removed.

H3 of the architecture conformance audit found this service with no
exception handling at all. Its one call site is in
ConversationOrchestrationService.run()'s finally block, which _try_catch never
covered (that only wraps _setup), so a raw OSError from the broker escaped
straight out of run().

No Validations mixin/file: the only input check is the empty-turns
short-circuit, which returns None rather than raising -- writing no log for
a session with no turns is a normal outcome, not a rejected input. Matches
FlagService's precedent of skipping a file that would be empty.

save()'s body is one inline nested closure passed straight to `_try_catch`
(defined in the Exceptions mixin) -- no separate `_do_thing` private method.
FileSessionLogBroker.write_session_log doesn't raise SessionLogUnavailableError
itself (it raises whatever raw OSError Path.write_text throws), so the
try/except that translates a raw broker failure into SessionLogUnavailableError
is preserved, just relocated inline inside the closure instead of a separate
`_save` method -- `_try_catch` then classifies that leaf into
SessionLogDependencyException the same as before.
"""

from pathlib import Path
from typing import List, Optional

from api.brokers.logging import LoggingBroker
from api.brokers.session_log import SessionLogBroker
from api.models.foundations.flag import Flag
from api.models.foundations.session_log.exceptions import SessionLogUnavailableError
from api.services.foundations.session_log.i_session_log_service import ISessionLogService
from api.services.foundations.session_log.session_log_service_exceptions import (
    SessionLogServiceExceptions,
)


class SessionLogService(SessionLogServiceExceptions, ISessionLogService):
    """Owns formatting + persistence of one session's end-of-run log."""

    def __init__(
        self,
        session_log_broker: SessionLogBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._session_log_broker = session_log_broker
        self._logging_broker = logging_broker

    def save(self, turns: List[str], flags: List[Flag]) -> Optional[Path]:
        def action() -> Optional[Path]:
            if not turns:
                return None

            output_lines = turns[:]
            if flags:
                output_lines.append("--- flags ---")
                for flag in flags:
                    output_lines.append(
                        f'[{flag.category}] said: "{flag.said}" -> corrected: "{flag.corrected}"'
                    )

            content = "\n".join(output_lines) + "\n"
            try:
                return self._session_log_broker.write_session_log(content)
            except Exception as e:
                raise SessionLogUnavailableError(str(e)) from e

        return self._try_catch(action)
