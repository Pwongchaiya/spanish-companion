# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-1054.md — Committed the
stop-flag polling fix (hardware-verified prior session, replacing the
unreliable Windows SIGBREAK graceful-stop mechanism), then built and
verified the last blocked piece of `app.py`: the `/api/events` SSE
endpoint (status/transcript/flags, per the architecture record's event
schema). Phase 2 build is now complete across all six features plus
`app.py` integration. Next session should start with the deferred test
pass (Ingestion, Retrieval, Generation, Review, Session Lifecycle HTTP
layer) plus adding `pytest` to `requirements.txt`, then frontend wiring
per feature.

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
