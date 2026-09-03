"""Foundation service for the live streaming transcript.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Shares SessionLogBroker
with SessionLogService (one broker, two Foundation concerns) -- this one
owns the live-transcript-file half. JSON-line formatting moved here
verbatim from _write_live_transcript's per-turn loop in
api/services/voice_conversation/voice_conversation_service.py.

No Validations/Exceptions mixin split: no validation beyond the broker's
own I/O, already covered by Voice Conversation's already-resolved
2-exception vocabulary (OSError -> VoiceConversationPipelineError at the
Orchestrator, unchanged from before this move).
"""

import json

from api.brokers.session_log import SessionLogBroker


class LiveTranscriptService:
    """Owns formatting + persistence of the live, in-progress transcript."""

    def __init__(self, session_log_broker: SessionLogBroker) -> None:
        self._session_log_broker = session_log_broker

    def clear(self) -> None:
        self._session_log_broker.clear_transcript()

    def append(self, role: str, text: str) -> None:
        line = json.dumps({"role": role, "text": text}, ensure_ascii=False)
        self._session_log_broker.append_transcript_line(line)
