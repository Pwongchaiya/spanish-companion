# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-0003.md — Closed out every
remaining Phase 2 architecture question. Resolved the `api`/`rag` package
split (two top-level packages, `api` depends on `rag`, never the reverse)
and corrected the internal layout to layer-first-then-feature
(`brokers/`, `models/`, `services/<feature>/`, `controllers/<feature>/`),
matching the user's `NL.Core.Entitlements` .NET reference project exactly.
Resolved the Phase 2 test strategy: pytest, three tiers (unit fully mocked,
integration real DB + mocked external APIs, acceptance full in-process
Flask app), modeled on that same reference project's "The Standard" testing
conventions, stdlib `unittest.mock` only. Committed the previously-untracked
`frontend/` Vite scaffold and created empty `api`/`rag`/`tests` directory
skeletons on disk. Nothing remains open before Phase 2 build starts — next
session should register the first entity (Session Lifecycle) via
`/new-entity`.

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
