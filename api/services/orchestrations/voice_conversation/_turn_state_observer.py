"""Pipecat frame filter: live turn-state signal for ConversationOrchestrator's
pipeline. Split out of voice_conversation_service.py, same reason as
_mic_gate.py.
"""

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)

from api.services.foundations.turn_state import ITurnStateService


class _TurnStateObserver:
    """Tracks the pipeline's live turn state (listening/thinking/speaking)
    from Bot/User *SpeakingFrame system frames and persists each
    transition via TurnStateService, for the frontend's SSE-driven turn
    indicator.

    Both frame pairs are broadcast upstream and downstream by pipecat (same
    mechanism _MicGate already relies on for BotStartedSpeakingFrame), so
    this observer sees them regardless of where in the pipeline it sits.
    Observe-only -- always passes every frame through unchanged.

    Needs filter_system_frames=True on the wrapping FunctionFilter, same
    reason as _MicGate: all four frame types are SystemFrames, which
    FunctionFilter auto-passes without invoking the filter otherwise.
    """

    def __init__(self, turn_state_service: ITurnStateService) -> None:
        self._turn_state_service = turn_state_service

    async def __call__(self, frame) -> bool:
        if isinstance(frame, UserStartedSpeakingFrame):
            self._turn_state_service.set("listening")
        elif isinstance(frame, UserStoppedSpeakingFrame):
            self._turn_state_service.set("thinking")
        elif isinstance(frame, BotStartedSpeakingFrame):
            self._turn_state_service.set("speaking")
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._turn_state_service.set("listening")
        return True
