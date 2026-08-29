"""Status snapshot for the voice-conversation session.

Mirrors the `SessionStatus` TypeScript interface already pinned for the
frontend in the Phase 2 architecture decision record — same three fields.
This dataclass is the backend source of truth; ConversationSessionService
(api/services/session_lifecycle.py) is the only producer.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionStatus:
    running: bool
    ready: bool
    graceful: Optional[bool]  # how the last session ended; None if never stopped
