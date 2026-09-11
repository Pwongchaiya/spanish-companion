"""Foundation service for the live streaming transcript.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Shares SessionLogBroker
with SessionLogService (one broker, two Foundation concerns) -- this one
owns the live-transcript-file half. JSON-line formatting moved here
verbatim from _write_live_transcript's per-turn loop in
api/services/orchestrations/voice_conversation/voice_conversation_service.py.

No composition step in __init__.py -- the concrete class is declared
directly in THIS file, inheriting the Exceptions mixin and the interface by
name. Matches LearnerProfileService's rebuilt shape exactly: one class,
declared once, `class X(XExceptions, IX):`, constructor and public methods
on it directly. (The previous `_LiveTranscriptServiceBase` + __init__.py
composition step was the invented-`_ServiceBase` pattern CLAUDE.md
explicitly disallows -- removed.)

H3 of the architecture conformance audit found this service with no
exception handling at all: append() is called from _write_live_transcript,
a background task that sits *outside* ConversationOrchestrationService's _try_catch
(which only wraps _setup), so a raw OSError from the broker escaped
straight into it. Every public method now routes through _try_catch.

Public methods are the ONLY thing that wraps with `_try_catch` (defined in
the Exceptions mixin) -- each public method's entire body is an inline
nested closure passed straight to `_try_catch`, not a separate `_do_thing`
private method with its own local try/except. No local try/except inside
the closures: the LiveTranscriptUnavailableError wrapping formerly done
inline is now raised in the closure itself, still propagating untouched to
`_try_catch`'s single dispatch point.

No Validations mixin/file: there is nothing to validate -- role and text
come from pipecat's own LLMContext, not from user input. Matches
FlagService's precedent of skipping a file that would be empty.
"""

import json

from api.brokers.logging import LoggingBroker
from api.brokers.session_log import SessionLogBroker
from api.models.foundations.live_transcript.exceptions import LiveTranscriptUnavailableError
from api.services.foundations.live_transcript.i_live_transcript_service import ILiveTranscriptService
from api.services.foundations.live_transcript.live_transcript_service_exceptions import (
    LiveTranscriptServiceExceptions,
)


class LiveTranscriptService(LiveTranscriptServiceExceptions, ILiveTranscriptService):
    """Owns formatting + persistence of the live, in-progress transcript."""

    def __init__(
        self,
        session_log_broker: SessionLogBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._session_log_broker = session_log_broker
        self._logging_broker = logging_broker

    def clear(self) -> None:
        def action() -> None:
            try:
                self._session_log_broker.clear_transcript()
            except Exception as e:
                raise LiveTranscriptUnavailableError(str(e)) from e

        self._try_catch(action)

    def append(self, role: str, text: str) -> None:
        def action() -> None:
            line = json.dumps({"role": role, "text": text}, ensure_ascii=False)
            try:
                self._session_log_broker.append_transcript_line(line)
            except Exception as e:
                raise LiveTranscriptUnavailableError(str(e)) from e

        self._try_catch(action)
