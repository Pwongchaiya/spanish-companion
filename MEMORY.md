# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-09-2240.md
Final `.claude-toolkit` audit: fixed a real data-loss bug (`--full` flush
archived only `### In flight`, destroying 4 of 5 checkpoint sections on
every `/session-end`), wired up 58 embedded self-checks that had never run
under any suite invocation (24→106 tests), fixed `sync_commands.py`
mirroring `__pycache__` bytecode into consumers, fixed `/project-init` still
instructing the symlink setup that caused this repo's own OneDrive
incident, and closed 5 README staleness items. Also built two generated
Obsidian canvases (`build_canvases.py`) for the toolkit workflow and the
session lifecycle, each validated against the toolkit tree it describes.
No entities touched, no application code.
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
