# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-04-1538.md — Session 8: tooling
only, no application code. Added YAML frontmatter to all 24 `.claude-toolkit`
skills in place (filenames unchanged, so the ~70 explicit-path agent
references still resolve) and shipped two runnable checks. Researched the
Claude Code ecosystem and captured a pre-refactor baseline: swear-jar is the
golden reference for layer shape, NL.Core.Users is authoritative for test
conventions. Measured a Broker Agent build at 10,350 mandatory skill tokens
with ~55% unused, and found three verified content defects in
`broker-skill.md` (ABC vs the Protocol waiver; a mislabeled interface sample;
async SQLAlchemy against a pg8000 sync stack). The skill refactor stands at
Phase 1.5 of 4 — Phase 2 (brainstorm) is next. Do not delete the control
worktree `.claude/worktrees/agent-aa34e1126e4b7e69e` before Phase 4.


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
