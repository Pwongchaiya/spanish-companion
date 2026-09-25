"""Broker for the flagged-grammar-error JSON file.

DB-backed flag storage is explicitly, deliberately deferred (see the Phase 2
architecture record) — this JSON file is a workaround for a real
pipecat/Windows shutdown-hang bug, not an oversight: Voice Conversation
(built later) must be able to flush flags to disk fast and synchronously
during signal-triggered shutdown, without waiting on a DB connection. This
ports Phase 1's `save_flags_json` / `load_latest_flags`
(`voice/bot.py`, `review/review.py`) semantics exactly, now behind a
Protocol so Review (built later) never depends on the file format directly.

Voice Conversation is the only writer of the flag *list*; Review is the only
reader. Since 2026-09-24 (Flag.status), Review is also a writer, but only of
one field on an existing row (`ReviewOrchestrationService.set_flag_status()`
loads the full list, replaces one flag's status, and calls `save_flags()`
with the full list back) — it never adds or removes a flag, and it still
goes through the same whole-file-overwrite `save_flags()` Voice Conversation
uses, not a separate partial-update method. Voice Conversation still
overwrites the whole file at the start of every session, so a status set in
Review only lasts until the next conversation starts.

No SQLAlchemy, no Alembic — there is no table backing this.
"""

from typing import Protocol

from api.models.foundations.flag import Flag


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
