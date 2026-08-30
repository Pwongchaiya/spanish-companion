"""JsonFileFlagBroker — JSON-file-backed FlagBroker."""

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from api.models.flag import Flag

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FLAGS_FILE = Path(os.getenv("FLAGS_FILE_PATH", str(REPO_ROOT / "data" / "flags.json")))


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
        # Atomic write (temp file + os.replace) so a concurrent load_flags()
        # never observes a truncated/partial file mid-write — write_text()
        # alone truncates then writes, a real window given Voice Conversation
        # rewrites this file every ~1s while Review could, in principle, read it.
        tmp_path = self._path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, self._path)

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
