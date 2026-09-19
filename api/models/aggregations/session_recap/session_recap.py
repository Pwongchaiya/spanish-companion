"""Domain model for the post-session recap card (roadmap item C2).

Computed on demand by SessionRecapAggregationService.get_latest_recap() from
two already-existing sources -- never persisted itself, same "read-only,
computed from other entities' rows" shape as SpeakingTotal/UnflaggedStreak
(api/models/orchestrations/progress/).

Field choice is deliberately narrower than a first-pass wishlist ("topics
touched", "mastered count") would suggest -- see
SessionRecapAggregationService's module docstring for why those two were
dropped rather than guessed at with an invented session link.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SessionRecap:
    """Plain data-carrier returned by get_latest_recap().

    `flag_count` and the session boundary timestamps come straight off the
    `session_log` row -- the count Voice Conversation itself wrote at
    session-end (`len(session_flags)`), not recomputed here.

    `categories_flagged` is the distinct, sorted set of `Flag.category`
    values from the CURRENT flags.json. That file is fully overwritten by
    `FlagService.save_flags(session_flags)` at the end of every session (see
    voice_conversation_service.py's `run()` finally-block), so "current
    flags" and "this session's flags" are the same list -- no session id,
    no timestamp-range join needed.
    """

    flag_count: int
    categories_flagged: List[str]
    session_started_at: datetime
    session_ended_at: Optional[datetime]
