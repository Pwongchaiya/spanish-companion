# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-05-1238.md — toolkit tooling only,
no application code. Landed Piece A of the session-lifecycle redesign's Stage
1 follow-up: `sync_state.py --full` now archives full ledger-segment text to
the session file and writes only pointers into state.md's Pending Work
(instead of raw ledger prose), with the archive write guarded so a failure
leaves the ledger intact. Wired into `session-end.md` as new Step 3b; deleted
two dead/redundant steps (6e, 7b). Committed to submodule + parent on
`fix/pwongchaiya/ledger-flush-data-loss` (not merged to main). `state.md`'s
Pending Work was corrupted by `obsidian_patch_content` + `operation: replace`
for a **third** time (sessions 9, 13, now this one) — this is no longer
"retry patch, fall back on failure": the standing rule is now **never**
patch this file, always `obsidian_put_content` full-rewrite. Also:
`obsidian_delete_file` on this file was silently auto-denied by the sandbox
classifier with no prompt reaching the user, so the documented
delete+recreate recovery path isn't reliably available either — `put_content`
alone is the dependable fix. Piece B (`state_md_guard.py`, N3 patch-vs-put
conflict) and Piece C (template reconciliation) remain deferred.


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
