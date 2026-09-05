# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-04-2352.md — Session 13: toolkit
tooling only, no application code. Fixed the toolkit skill refactor Phase 3's
last known defect (async/await used directly on the now-sync `Session` in
`storage-broker-implementation-pattern-sqlalchemy.md` — bridged via
`asyncio.to_thread`), so Phase 3 is now fully complete. Landed Stage 1 of a
5-stage session-lifecycle redesign (plan:
`C:\Users\pwong\.claude\plans\quiet-juggling-music.md`): append-only
checkpoint ledger + shared `scripts/sync_state.py` (8 tests) replacing
`/checkpoint`'s old destructive-overwrite Step 1c. Reproduced a
stale-command-cache bug for the second time (a Skill loads a cached copy of a
command file just edited this session, not the real one on disk) — not yet
fixed, workaround is to `Read` the actual file first. `state.md`'s Pending
Work section was corrupted again by `obsidian_patch_content` +
`operation: replace` (same failure mode as session 9) and recovered via full
`put_content` rewrite — do not use `replace` on that file's headings.


## Entity Manifest

| Feature | Path |
| --- | --- |
| SessionLifecycle | Projects/spanish-companion/entities/session-lifecycle.md |
| VoiceConversation | Projects/spanish-companion/entities/voice-conversation.md |
| Ingestion | Projects/spanish-companion/entities/ingestion.md |
| Retrieval | Projects/spanish-companion/entities/retrieval.md |
| Generation | Projects/spanish-companion/entities/generation.md |
| Review | Projects/spanish-companion/entities/review.md |

---

## Vault Structure Reference

| Location | Path | What lives there |
| --- | --- | --- |
| Project state | Projects/spanish-companion/state.md | MVP stage tracker, pending work, last session pointer |
| Session summaries | Projects/spanish-companion/sessions/ | One file per session — YYYY-MM-DD-HHmm.md |
| Architectural decisions | Projects/spanish-companion/decisions/ | One file per decision — kebab-case slug |
