"""Foundation service for the live turn-state signal.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. Shares SessionLogBroker
with SessionLogService/LiveTranscriptService (one broker, three Foundation
concerns) -- this one owns the turn-state-file third.

No Validations/Exceptions mixin split: no validation beyond the broker's
own I/O, same reasoning as LiveTranscriptService.
"""

from api.brokers.session_log import SessionLogBroker


class TurnStateService:
    """Owns persistence of the pipeline's current turn state
    (listening/thinking/speaking), for the frontend's SSE-driven
    turn indicator."""

    def __init__(self, session_log_broker: SessionLogBroker) -> None:
        self._session_log_broker = session_log_broker

    def set(self, state: str) -> None:
        self._session_log_broker.write_turn_state(state)
