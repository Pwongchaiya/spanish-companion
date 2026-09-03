# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-03-1434.md — tooling/documentation
session, not layer-build work: added a "Codebase Documentation (repowise)"
section to CLAUDE.md (when to use repowise's MCP tools vs. plain Grep/Read,
staleness caveat), committed alongside a pending `.claude-toolkit` submodule
bump. Built a new global (not project-scoped) `revise-prompt` skill at
`~/.claude/skills/revise-prompt/` that rewrites a raw prompt before acting on
it, then corrected it twice after live use surfaced real bugs in its own
design (an over-narrow "ask only for genuine forks" gate, and "show the
revision" collapsing into the same turn as acting with no real pause). No
spanish-companion entities or layers touched. Six-layer rebuild (Waves 1-7 of
9, landed 2026-09-02) and the hackathon-prep decision points are unchanged
this session — see Projects/spanish-companion/decisions/six-layer-standard-rebuild.md
and Projects/spanish-companion/decisions/hackathon-nerdy-plan-of-attack.md.

---

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
