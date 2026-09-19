"""Broker for the practice-attempt JSON Lines log.

DB-backed persistence is deferred the same way `api/brokers/flag/`'s flag
storage is (see that package's `i_flag_broker.py` docstring for the
pipecat/Windows shutdown-hang rationale) — a plain append-only file means a
practice attempt is durable the instant it's written, no DB round-trip
required.

New in Phase 2: Phase 1's practice log (`review/review.py`'s
`record_practice()`) wrote one throwaway `.log` file per attempt with no
read path at all. `PracticeAttempt.flag_id` (referencing `Flag.id` in
`api/models/flag.py`) gives Review (built later) something durable to read
attempts back by.

`PracticeAttempt` is defined here, not in `api/models/` — it's this
broker's own record shape, not a shared domain model. No SQLAlchemy, no
Alembic — there is no table backing this.

A2 (graded practice-attempt verdict): `grade` is an additive field on this
existing dataclass/file format — no migration needed, since no SQL table
backs it. A JSONL row written before this change has no "grade" key; the
concrete broker's `read_attempts()` defaults a missing key to "again" (the
same conservative fallback the judge itself uses) rather than raising.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class PracticeAttempt:
    flag_id: str  # plain str — do not import Flag here, see module docstring
    attempt_text: str
    timestamp: datetime
    grade: str  # one of "again" | "hard" | "good" | "easy" -- see GenerationService.judge_practice_attempt


class PracticeLogBroker(Protocol):
    """External-resource boundary for practice-attempt persistence. Raw
    JSON Lines file I/O only — no business logic."""

    def record_attempt(self, attempt: PracticeAttempt) -> None:
        """Append one JSON object per line (JSON Lines), append-only."""
        ...

    def read_attempts(self, flag_id: str | None = None) -> list[PracticeAttempt]:
        """All attempts, or only one flag_id's if given. New capability —
        Phase 1 had no read path at all for its plain-text practice log."""
        ...
