"""Foundation service for the live streaming transcript.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Shares SessionLogBroker
with SessionLogService (one broker, two Foundation concerns) -- this one
owns the live-transcript-file half. JSON-line formatting moved here
verbatim from _write_live_transcript's per-turn loop in
api/services/orchestrations/voice_conversation/voice_conversation_service.py.

Split into a base logic file plus an Exceptions mixin
(live_transcript_service_exceptions.py), combined into the concrete
LiveTranscriptService in __init__.py -- mirrors FlagService's shape, which
in turn mirrors C#'s `partial class`.

H3 of the architecture conformance audit found this service with no
exception handling at all: append() is called from _write_live_transcript,
a background task that sits *outside* ConversationOrchestrator's _try_catch
(which only wraps _setup), so a raw OSError from the broker escaped
straight into it. Every public method now routes through _try_catch.

No Validations mixin/file: there is nothing to validate -- role and text
come from pipecat's own LLMContext, not from user input. Matches
FlagService's precedent of skipping a file that would be empty.
"""

import json

from api.brokers.logging import LoggingBroker
from api.brokers.session_log import SessionLogBroker
from api.models.live_transcript.exceptions import LiveTranscriptUnavailableError


class _LiveTranscriptServiceBase:
    """Owns formatting + persistence of the live, in-progress transcript.

    Public methods delegate to a private `_do_thing` method through
    `_try_catch` (defined in the Exceptions mixin), per
    python-adaptations-skill.md's TryCatch translation.
    """

    def __init__(
        self,
        session_log_broker: SessionLogBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._session_log_broker = session_log_broker
        self._logging_broker = logging_broker

    def clear(self) -> None:
        self._try_catch(self._clear)

    def _clear(self) -> None:
        try:
            self._session_log_broker.clear_transcript()
        except Exception as e:
            raise LiveTranscriptUnavailableError(str(e)) from e

    def append(self, role: str, text: str) -> None:
        self._try_catch(lambda: self._append(role, text))

    def _append(self, role: str, text: str) -> None:
        line = json.dumps({"role": role, "text": text}, ensure_ascii=False)
        try:
            self._session_log_broker.append_transcript_line(line)
        except Exception as e:
            raise LiveTranscriptUnavailableError(str(e)) from e
