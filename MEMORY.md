# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-04-1644.md — Session 9: tooling
only, no application code. Verified every source the toolkit refactor tests
against before acting on it (control worktree intact at exactly 27 generated
files; swear-jar; NL.Core.Users under `source/repos/`, not Documents) and
re-confirmed the three `broker-skill.md` defects independently against disk.
**Phase 2 of the skill refactor is now DECIDED** — six settled constraints,
recorded in `wiki/decisions/toolkit-skill-refactor-phase-2-decisions.md`:
split by heading name; `references/<skill>/` plus one shared file; Import
Scaffolding becomes a `scripts/` generator; Style A agents keep the mandatory
load list; extend `verify_frontmatter.py`; and **split first, then fix
D1-D3**. Scope is 19 skills (the 5 `rag-*` are out). **Phase 3 (write the
plan) is next.** Also fixed a real gap: the project had no `SessionStart`
hook, so `/checkpoint` never auto-injected despite claiming it would. Two
corrections logged — the baseline's NL.Core.Users count is 128, not 122, and
`/next-session-prompt` is not blocked by its freshness check after
`/checkpoint` (the real conflict is that `/checkpoint` leaves `state.md`
untouched). Do not delete the control worktree
`.claude/worktrees/agent-aa34e1126e4b7e69e` before Phase 4.


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
