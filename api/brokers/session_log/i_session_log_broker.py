"""Broker for Voice Conversation's three file-writing concerns: the
end-of-session review log, the live streaming transcript (Review Mode /
SSE), and the live turn-state signal (SSE). Two Foundation services sit in
front of it (SessionLogService, LiveTranscriptService) -- each owns one
concern's validation/formatting, this broker does only the raw file I/O.
The turn-state signal has no service: W3 of the architecture conformance
audit deleted TurnStateService as a pure pass-through (M5), so
ConversationOrchestrationService and _TurnStateObserver call write_turn_state()
here directly.
"""

from pathlib import Path
from typing import Protocol


class SessionLogBroker(Protocol):
    """External-resource boundary for session-log/transcript file I/O. Raw
    I/O only -- no formatting, no business logic."""

    def write_session_log(self, content: str) -> Path:
        """Write `content` to a new timestamped log file, returning its path."""
        ...

    def clear_transcript(self) -> None:
        """Truncate (or create) the live transcript file, empty."""
        ...

    def append_transcript_line(self, line: str) -> None:
        """Append one already-formatted line to the live transcript file."""
        ...

    def write_turn_state(self, state: str) -> None:
        """Overwrite the turn-state file with the pipeline's current turn
        state (listening/thinking/speaking), for /api/events."""
        ...
