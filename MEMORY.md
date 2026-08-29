# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-0953.md — Pinned the
shared broker method surfaces, registered all six Phase 2 features, then
built nearly the entire backend via a parallel multi-agent orchestration
(Opus-designed 7-wave dependency graph): SessionLifecycle, Ingestion,
Retrieval, Generation, and Review are all Broker/Service/Controller
complete, `app.py` wires Session Lifecycle + Review (verified via Flask's
test client), and Voice Conversation's code (manual port) is written but
NOT hardware/mic verified. Auditor passes caught real bugs at every wave;
one bug (`ALLOWED_ORIGINS` missing `127.0.0.1`) was caught live by the
user. Testing was explicitly deferred mid-build across all six features.
Next session should start with the Voice Conversation hardware/mic test.

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
