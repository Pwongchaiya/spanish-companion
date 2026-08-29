"""Broker for the practice-attempt JSON Lines log.

DB-backed persistence is deferred the same way `api/brokers/flag.py`'s flag
storage is (see that module's docstring for the pipecat/Windows
shutdown-hang rationale) — a plain append-only file means a practice
attempt is durable the instant it's written, no DB round-trip required.

New in Phase 2: Phase 1's practice log (`review/review.py`'s
`record_practice()`) wrote one throwaway `.log` file per attempt with no
read path at all. `PracticeAttempt.flag_id` (referencing `Flag.id` in
`api/models/flag.py`) gives Review (built later) something durable to read
attempts back by.

`PracticeAttempt` is defined here, not in `api/models/` — it's this
broker's own record shape, not a shared domain model. No SQLAlchemy, no
Alembic — there is no table backing this.
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRACTICE_LOG_FILE = Path(
    os.getenv("PRACTICE_LOG_FILE_PATH", str(REPO_ROOT / "data" / "practice_log.jsonl"))
)


@dataclass
class PracticeAttempt:
    flag_id: str  # plain str — do not import Flag here, see module docstring
    attempt_text: str
    timestamp: datetime


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


class JsonLinesPracticeLogBroker:
    """PracticeLogBroker backed by a JSON Lines file, appended to on every
    record.

    `path` defaults to PRACTICE_LOG_FILE_PATH (env) and is only overridden
    by callers that want an isolated file (e.g. tests, once written).
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else DEFAULT_PRACTICE_LOG_FILE

    def record_attempt(self, attempt: PracticeAttempt) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({**asdict(attempt), "timestamp": attempt.timestamp.isoformat()}, ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read_attempts(self, flag_id: str | None = None) -> list[PracticeAttempt]:
        # ponytail: same missing-file tolerance as FlagBroker.load_flags —
        # nothing recorded yet is not an error. utf-8-sig for the same
        # PowerShell-BOM reason as flag.py's load_flags (only the first
        # line could ever carry one, but it's cheap to always tolerate it).
        try:
            lines = self._path.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            return []
        attempts = []
        for line in lines:
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                attempt = PracticeAttempt(
                    flag_id=raw["flag_id"],
                    attempt_text=raw["attempt_text"],
                    timestamp=datetime.fromisoformat(raw["timestamp"]),
                )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if flag_id is None or attempt.flag_id == flag_id:
                attempts.append(attempt)
        return attempts
