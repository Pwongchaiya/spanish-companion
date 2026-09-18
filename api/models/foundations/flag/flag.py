"""Domain model for a single flagged grammar error.

Voice Conversation (built later) creates these during live conversation as a
byproduct of the same Gemini generation call that produces the response —
Phase 1's flagging behavior, ported as-is (see `voice/bot.py`'s
`save_flags_json` and `review/review.py`'s `load_latest_flags`).

`id` and `timestamp` are new in Phase 2 — confirmed user decision, not an
invented field. Phase 1 addressed flags by list position only, which breaks
as soon as something needs to reference one durably: the frontend needs a
stable React key for the SSE `flags` push, and `PracticeAttempt.flag_id`
(`api/brokers/practice_log.py`) needs something to link a practice attempt
back to the flag it was practicing.

`channel` and `occurrence_count` are new 2026-09-18 (A7+B3, confirmed user
decision) — default to "grammar"/1 so every pre-existing Flag(...) call site
and every already-saved flags.json row keeps working untouched. `channel`
distinguishes what kind of mistake this is (grammar | lexis | pronunciation |
orthography); Voice Conversation drops orthography-channel flags before they
ever reach this dataclass, since a spoken session can't legitimately produce
one (see voice_conversation_service.py's `_record_flag`). `occurrence_count`
collapses repeat flags for the same (category, said, corrected) within one
session instead of one row per repeat.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Flag:
    id: str  # uuid4 hex, generated at flag-creation time by Voice Conversation
    said: str
    corrected: str
    category: str
    timestamp: datetime
    channel: str = "grammar"
    occurrence_count: int = 1
