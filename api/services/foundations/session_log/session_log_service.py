"""Foundation service for the end-of-session review log.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Formatting logic
(save_session_log's body) moved here verbatim from
api/services/orchestrations/voice_conversation/voice_conversation_service.py
-- the Orchestrator still owns flattening LLMContext into `turns` (a
pipecat-specific concern this Foundation shouldn't need to know about), and
passes already-flattened strings in.

Split into a base logic file plus an Exceptions mixin
(session_log_service_exceptions.py), combined into the concrete
SessionLogService in __init__.py -- mirrors FlagService's shape, which in
turn mirrors C#'s `partial class`.

H3 of the architecture conformance audit found this service with no
exception handling at all. Its one call site is in
ConversationOrchestrator.run()'s finally block, which _try_catch never
covered (that only wraps _setup), so a raw OSError from the broker escaped
straight out of run().

No Validations mixin/file: the only input check is the empty-turns
short-circuit, which returns None rather than raising -- writing no log for
a session with no turns is a normal outcome, not a rejected input. Matches
FlagService's precedent of skipping a file that would be empty.
"""

from pathlib import Path
from typing import List, Optional

from api.brokers.logging import LoggingBroker, StdlibLoggingBroker
from api.brokers.session_log import SessionLogBroker
from api.models.flag import Flag
from api.models.session_log.exceptions import SessionLogUnavailableError


class _SessionLogServiceBase:
    """Owns formatting + persistence of one session's end-of-run log.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per
    python-adaptations-skill.md's TryCatch translation.
    """

    def __init__(
        self,
        session_log_broker: SessionLogBroker,
        logging_broker: LoggingBroker = StdlibLoggingBroker(),
    ) -> None:
        self._session_log_broker = session_log_broker
        self._logging_broker = logging_broker

    def save(self, turns: List[str], flags: List[Flag]) -> Optional[Path]:
        return self._try_catch(lambda: self._save(turns, flags))

    def _save(self, turns: List[str], flags: List[Flag]) -> Optional[Path]:
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
