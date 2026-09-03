# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-03-1650.md — app-hardening pass,
explicitly reprioritized over hackathon submission logistics this session
(Sep 18 deadline may now slip). Landed Wave 8 (Voice Conversation six-layer
migration — 3 new Brokers, 4 new Foundations, Orchestrator rewired onto 5
Foundation deps, zero behavior change verified), plus a same-day follow-up
fix (user caught that the Orchestrator/CLI entrypoint were left at old flat
paths — moved to `services/orchestrations/voice_conversation/` and
`exposers/voice_conversation.py`, `api/controllers/` now fully retired).
Also: a real pipeline-setup-timeout bug found and fixed (was silently
exiting 0 instead of crashing), `pipecat-ai` pinned to `==1.8.1`, Flag/
PracticeLog/ChunkRepository/EmbeddingModel got full test coverage for the
first time, Tri-Nature gaps 1+2 closed (Judge for Generation, prompts
extracted to data files), 6+ dead files/folders removed. Two commits:
`b88ef76`, `9f13120`. See
Projects/spanish-companion/decisions/wave-8-voice-conversation-six-layer-migration.md.

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
