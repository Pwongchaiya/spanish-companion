"""Foundation service for the end-of-session review log.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Formatting logic
(save_session_log's body) moved here verbatim from
api/services/voice_conversation/voice_conversation_service.py -- the
Orchestrator still owns flattening LLMContext into `turns` (a pipecat-
specific concern this Foundation shouldn't need to know about), and passes
already-flattened strings in.

No Validations/Exceptions mixin split: the only "validation" is the
empty-turns short-circuit, already a one-line guard, and the underlying
broker call raises no leaf this feature's already-resolved 2-exception
vocabulary doesn't already cover raw (OSError -> VoiceConversationPipelineError
at the Orchestrator, unchanged from before this move).
"""

from pathlib import Path
from typing import List, Optional

from api.brokers.session_log import SessionLogBroker
from api.models.flag import Flag


class SessionLogService:
    """Owns formatting + persistence of one session's end-of-run log."""

    def __init__(self, session_log_broker: SessionLogBroker) -> None:
        self._session_log_broker = session_log_broker

    def save(self, turns: List[str], flags: List[Flag]) -> Optional[Path]:
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
        return self._session_log_broker.write_session_log(content)
