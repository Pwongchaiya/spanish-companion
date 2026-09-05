# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-05-1320.md — toolkit tooling only,
no application code. Closed Pieces A+B of the session-lifecycle redesign:
`session-end.md` Step 6 rewritten to always do a single
`obsidian_get_file_contents` + `obsidian_put_content` for state.md, never
`patch_content`/`delete_file` (patch had corrupted this file 3x — sessions 9,
13, and last session). Built `.claude-toolkit/.claude/hooks/state_md_guard.py`
(9 passing tests) as the actual enforcement — a PostToolUse hook that
re-reads state.md from disk after any write and flags a duplicate heading or
an over-25-line Pending Work section; wired into this project's
`.claude/settings.local.json`. Also fixed while restructuring the command
(418→316 lines): `{OBSIDIAN_VAULT_PATH}` in Step 3b now resolves from
`settings.local.json` instead of being guessed, and Step 5's entity template
now reads the canonical `Projects/_templates/entity-tracker.md` (the inline
copy was missing frontmatter). Decision record:
`wiki/decisions/session-end-state-md-guard.md`. Piece C (template
reconciliation) remains open. **`.claude-toolkit` changes are staged but
deliberately uncommitted this session — held for user review on request.**
Also hit the documented stale-command-cache bug a third time (Skill tool
served the pre-edit session-end.md) — worked around by reading the file
directly, as state.md's Pending Work already prescribes.


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
