"""JsonFileFlagBroker — JSON-file-backed FlagBroker."""

import json
import os
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from api.models.foundations.flag import Flag

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FLAGS_FILE = Path(os.getenv("FLAGS_FILE_PATH", str(REPO_ROOT / "data" / "flags.json")))


def _parse_flags(raw: object) -> list[Flag]:
    # ponytail: tolerant parsing is the spec, not error-hiding — mirrors
    # Phase 1's load_latest_flags() so Review never crashes on a missing
    # file, one caught mid-write, or a stale Phase 1-shaped file. Shared by
    # load_flags() and get_session_flags() -- same file shape, same rules.
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
                    # .get() with the dataclass default, not item[...] --
                    # a flags.json written before 2026-09-18 (A7+B3) has
                    # neither key, and that's not malformed data. Same
                    # tolerance for "status" (new 2026-09-24): a row
                    # written before that date has no status key either.
                    channel=item.get("channel", "grammar"),
                    occurrence_count=item.get("occurrence_count", 1),
                    status=item.get("status", "open"),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return flags


def _atomic_write(path: Path, payload: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write (temp file + os.replace) so a concurrent load never
    # observes a truncated/partial file mid-write — write_text() alone
    # truncates then writes, a real window given Voice Conversation rewrites
    # flags.json every ~1s while Review could, in principle, read it.
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # ponytail: OneDrive syncs this repo and transiently locks files it's
    # actively uploading, raising WinError 5 on os.replace. flags.json is
    # rewritten every ~1s during a session, so it collides with OneDrive
    # often enough to matter. Retry a few times before giving up.
    for attempt in range(5):
        try:
            os.replace(tmp_path, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


class JsonFileFlagBroker:
    """FlagBroker backed by a single JSON file, fully overwritten on every
    save.

    `path` defaults to FLAGS_FILE_PATH (env) and is only overridden by
    callers that want an isolated file (e.g. tests, once written).

    Per-session snapshots (save_session_flags/get_session_flags, added
    2026-09-24 for E3 replay) live in a `flags/` directory next to `path` --
    `<path.parent>/flags/session_<id>.json` -- so tests that override `path`
    get an isolated session directory too, for free.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else DEFAULT_FLAGS_FILE
        self._session_dir = self._path.parent / "flags"

    def _session_path(self, session_id: int) -> Path:
        return self._session_dir / f"session_{session_id}.json"

    def save_flags(self, flags: list[Flag]) -> None:
        payload = [{**asdict(flag), "timestamp": flag.timestamp.isoformat()} for flag in flags]
        _atomic_write(self._path, payload)

    def load_flags(self) -> list[Flag]:
        # utf-8-sig (not utf-8) because PowerShell can write a BOM on
        # Windows, same reason review/review.py:48 uses it.
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return []
        return _parse_flags(raw)

    def save_session_flags(self, session_id: int, flags: list[Flag]) -> None:
        payload = [{**asdict(flag), "timestamp": flag.timestamp.isoformat()} for flag in flags]
        _atomic_write(self._session_path(session_id), payload)

    def get_session_flags(self, session_id: int) -> list[Flag] | None:
        try:
            raw = json.loads(self._session_path(session_id).read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(raw, list):
            return None
        return _parse_flags(raw)


if __name__ == "__main__":
    # ponytail: self-check for the retry loop, not a broker-tier pytest suite
    # (this project's test strategy deliberately has none, see
    # decisions/companion-architecture-broker-service-controller.md).
    import tempfile
    from unittest.mock import patch

    from api.models.foundations.flag import Flag

    with tempfile.TemporaryDirectory() as tmp_dir:
        broker = JsonFileFlagBroker(path=Path(tmp_dir) / "flags.json")
        flags = [Flag(id="1", said="hablo", corrected="hablé", category="tense", timestamp=datetime.now())]

        calls = {"n": 0}
        real_replace = os.replace

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] < 3:
                raise PermissionError("simulated OneDrive lock")
            return real_replace(src, dst)

        with patch("os.replace", side_effect=flaky_replace):
            broker.save_flags(flags)
        assert calls["n"] == 3, f"expected 2 failures then a success, got {calls['n']} calls"
        assert [f.id for f in broker.load_flags()] == ["1"]

        with patch("os.replace", side_effect=PermissionError("still locked")):
            try:
                broker.save_flags(flags)
                raise AssertionError("expected PermissionError to propagate after exhausting retries")
            except PermissionError:
                pass

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Pre-2026-09-18 flags.json has neither "channel" nor
        # "occurrence_count" -- confirms load_flags() defaults them instead
        # of dropping the row (KeyError would hit the except (KeyError,
        # TypeError, ValueError): continue branch above and silently lose it).
        old_format_path = Path(tmp_dir) / "flags.json"
        old_format_path.write_text(
            json.dumps(
                [
                    {
                        "id": "1",
                        "said": "hablo",
                        "corrected": "hablé",
                        "category": "tense",
                        "timestamp": "2026-08-01T12:00:00",
                    }
                ]
            ),
            encoding="utf-8",
        )
        loaded = JsonFileFlagBroker(path=old_format_path).load_flags()
        assert len(loaded) == 1
        assert loaded[0].channel == "grammar"
        assert loaded[0].occurrence_count == 1
        # "status" is the same tolerance, added 2026-09-24 -- a row without
        # it loads as "open" instead of being dropped.
        assert loaded[0].status == "open"

    with tempfile.TemporaryDirectory() as tmp_dir:
        # status round-trips through save_flags -> load_flags unchanged.
        broker = JsonFileFlagBroker(path=Path(tmp_dir) / "flags.json")
        flag = Flag(
            id="1", said="hablo", corrected="hablé", category="tense", timestamp=datetime.now(), status="mastered"
        )
        broker.save_flags([flag])
        loaded = broker.load_flags()
        assert len(loaded) == 1
        assert loaded[0].status == "mastered"

    with tempfile.TemporaryDirectory() as tmp_dir:
        # save_session_flags/get_session_flags (added 2026-09-24 for E3
        # replay) round-trip independently of flags.json, and get_session_flags
        # returns None -- not [] -- for a session with no snapshot, so a
        # caller can tell "no flags this session" apart from "no file yet".
        broker = JsonFileFlagBroker(path=Path(tmp_dir) / "flags.json")
        session_flag = Flag(
            id="s1", said="tengo hambre", corrected="tengo hambre", category="lexis", timestamp=datetime.now()
        )
        assert broker.get_session_flags(4) is None

        broker.save_session_flags(4, [session_flag])
        loaded_session = broker.get_session_flags(4)
        assert loaded_session is not None and [f.id for f in loaded_session] == ["s1"]
        # flags.json itself is untouched by a per-session write.
        assert broker.load_flags() == []
        # another session's snapshot stays isolated.
        assert broker.get_session_flags(5) is None

    print("flag_broker self-check passed")
