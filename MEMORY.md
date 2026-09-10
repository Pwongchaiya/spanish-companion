# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-09-2154.md
Audited `.claude-toolkit/.claude/commands/` (10 files, 1813 lines). 9/10 had
no `description:` frontmatter and 7 wrapped their body in a stray
```markdown fence, so the command listing rendered "```markdown" instead of
a description. Fixed, plus 2 descriptions that broke plain-YAML parsing on
an inline `: `, `{slug}`/`{project-name}` normalized to `{project}`, and two
out-of-order steps renumbered. `sync_commands.py` now rejects a `--root`
that isn't a `.claude` dir — root cause of 3 stray untracked copies
(`commands/`, `agents/`, `skills/`) found and deleted. Guard tests 3→7,
all pass. No entities touched, no application code.
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
