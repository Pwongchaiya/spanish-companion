"""Broker for the flagged-grammar-error JSON file.

DB-backed flag storage is explicitly, deliberately deferred (see the Phase 2
architecture record) — this JSON file is a workaround for a real
pipecat/Windows shutdown-hang bug, not an oversight: Voice Conversation
(built later) must be able to flush flags to disk fast and synchronously
during signal-triggered shutdown, without waiting on a DB connection. This
ports Phase 1's `save_flags_json` / `load_latest_flags`
(`voice/bot.py`, `review/review.py`) semantics exactly, now behind a
Protocol so Review (built later) never depends on the file format directly.

Voice Conversation is the only writer; Review is the only reader. No
SQLAlchemy, no Alembic — there is no table backing this.
"""

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from api.models.flag import Flag

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FLAGS_FILE = Path(os.getenv("FLAGS_FILE_PATH", str(REPO_ROOT / "data" / "flags.json")))


class FlagBroker(Protocol):
    """External-resource boundary for flag persistence. Raw JSON-file I/O
    only — no business logic. Voice Conversation and Review compose this
    themselves; this broker just does the read/write."""

    def save_flags(self, flags: list[Flag]) -> None:
        """Overwrite the file with the FULL current list, always — even when
        empty. Matches Phase 1's save_flags_json() semantics exactly, so
        Review (built later) never reads stale data. Voice Conversation
        (built later) is the only writer."""
        ...

    def load_flags(self) -> list[Flag]:
        """[] on missing file, non-list JSON, or parse error — same
        tolerance as Phase 1's load_latest_flags(). Review is the only
        reader."""
        ...


class JsonFileFlagBroker:
    """FlagBroker backed by a single JSON file, fully overwritten on every
    save.

    `path` defaults to FLAGS_FILE_PATH (env) and is only overridden by
    callers that want an isolated file (e.g. tests, once written).
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else DEFAULT_FLAGS_FILE

    def save_flags(self, flags: list[Flag]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [{**asdict(flag), "timestamp": flag.timestamp.isoformat()} for flag in flags]
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_flags(self) -> list[Flag]:
        # ponytail: tolerant parsing is the spec, not error-hiding — mirrors
        # Phase 1's load_latest_flags() so Review never crashes on a
        # missing file, one caught mid-write, or a stale Phase 1-shaped
        # file. utf-8-sig (not utf-8) because PowerShell can write a BOM on
        # Windows, same reason review/review.py:48 uses it.
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(raw, list):
            return []
        flags = []
        for item in raw:
            try:
                flags.append(
                    Flag(
                        id=item["id"],
                        said=item["said"],
                        corrected=item["corrected"],
                        category=item["category"],
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return flags
