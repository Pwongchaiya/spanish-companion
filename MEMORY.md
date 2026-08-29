# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-1235.md — Wired the React
frontend (Conversation + Review views) to the live backend per the
architecture record's hook-layering spec: api/client.ts, Zustand store,
useEventSource/useSessionState/useReviewFlow hooks. Verified end-to-end
against a real Flask backend (start/stop, SSE transcript, flag select,
RAG-grounded explanation, practice submission). Along the way, found and
fixed a local dev-DB gap (Alembic migration `0001` had never been applied
here) and re-ingested the 39-chunk starter corpus. Committed `ae61440`.
This was the last unassigned Phase 2 build-order item — nothing blocking
for next session.

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
