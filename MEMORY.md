# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-03-2042.md — Tri-Nature Gate
(gap #3) resolved as a documented refusal via the Brainstorm Agent: no
adversary exists on Voice Conversation's transcript-content path, today or
post-deployment (the real future adversary hits the HTTP/API layer). All 3
Tri-Nature gaps now closed (2 built, 1 refused). See
Projects/spanish-companion/decisions/tri-nature-gate-design.md. The Gate
brainstorm's actual motivating symptom (bot goes quiet in a noisy room)
turned out to be a VAD/latency bug — fixed (`VAD_STOP_SECS`, env-configurable,
default 0.5s vs. Silero's stock 0.2s) — plus a new live listening/thinking/
speaking indicator built end to end (`TurnStateService` Foundation, `/api/events`
SSE, `ConversationView`). Also fixed 3 user-identified architecture deviations
in Voice Conversation's Orchestration layer (missing interface file, helper
classes bundled into one file, no exceptions mixin) to match Session
Lifecycle/Review's shape: added `VoiceConversationService` Protocol, split
`_MicGate`/`_TurnStateObserver` into their own files, added
`ConversationOrchestratorExceptions` mixin (`_try_catch` pattern). 131/131
unit tests pass. Two commits: `2d2aa87`, `03bbc67`.

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
