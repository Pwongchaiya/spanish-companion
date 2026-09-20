"""Interface for the Session Replay orchestration service (roadmap E3).

typing.Protocol per this project's interface waiver. Both methods raise
SessionReplayOrchestrationValidationException (a missing audio row or missing
session surfaces as a NotFound leaf somewhere down its `inner_exception`
chain), SessionReplayOrchestrationDependencyException, or
SessionReplayOrchestrationServiceException.
"""

from typing import Protocol

from api.models.foundations.session_audio.session_audio import SessionAudio
from api.models.orchestrations.session_replay.session_replay import SessionReplay


class ISessionReplayService(Protocol):
    """External-facing contract for replay assembly."""

    def get_replay(self, session_log_id: int) -> SessionReplay:
        """Audio duration plus this session's flags placed on its timeline."""
        ...

    def get_audio(self, session_log_id: int) -> SessionAudio:
        """The session's audio row (file path for streaming)."""
        ...
