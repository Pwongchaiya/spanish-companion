"""JsonLinesPracticeLogBroker — JSON-Lines-file-backed PracticeLogBroker."""

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from api.brokers.practice_log.i_practice_log_broker import PracticeAttempt

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PRACTICE_LOG_FILE = Path(os.getenv("PRACTICE_LOG_FILE_PATH", str(REPO_ROOT / "data" / "practice_log.jsonl")))


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
        # PowerShell-BOM reason as flag/flag_broker.py's load_flags (only
        # the first line could ever carry one, but it's cheap to always
        # tolerate it).
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
                    # A2: additive field -- a row written before the graded
                    # verdict shipped has no "grade" key. Default to "again",
                    # the same conservative fallback the judge itself uses.
                    grade=raw.get("grade", "again"),
                )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if flag_id is None or attempt.flag_id == flag_id:
                attempts.append(attempt)
        return attempts
