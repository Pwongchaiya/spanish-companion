"""Read model returned by SessionReplayOrchestrationService (roadmap E3)."""

from dataclasses import dataclass


@dataclass
class ReplayFlag:
    """One flag placed on the audio timeline. `offset_seconds` is the flag's
    timestamp minus the session's started_at."""

    flag_id: str
    offset_seconds: float
    said: str
    corrected: str
    category: str


@dataclass
class SessionReplay:
    session_log_id: int
    duration_seconds: float
    flags: list[ReplayFlag]
