# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-09-2032.md
session-lifecycle work, no application code. Landed L2 (`/session-end` now
carries a 7-turn batching table against a measured 20) and closed L6 in both
halves: `state_md_guard.py` exits 2 on stderr so its warnings reach the model,
and `/checkpoint` no longer writes `state.md` at all — `sync_state.py --full`
is the only writer. 8 files, -128 net lines, all 12 toolkit self-checks pass.
L1/L2 stay unverified until `lifecycle_cost.py` has post-fix runs; this
session is n=4. See wiki/decisions/pending-work-single-writer.md.
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
