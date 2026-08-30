# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-30-0135.md — Planning-only
session, no code changed. User asked to reverse Phase 2's 3-layer
(Broker→Service→Controller) collapse back to the full Standard six-layer
pattern (Broker→Foundation→Processing→Orchestration→Aggregation→Exposer),
treating this as a production-ready build. Two Explore agents read actual
api/rag source directly (CLAUDE.md/Obsidian carried a repowise staleness
warning) for exact ground truth on every Service/Broker/exception/call
chain; a Plan agent designed the full rebuild against that ground truth,
verified against review_service.py/app.py, then approved. Inserts genuine
Foundation services under Ingestion, Retrieval, and Review (closing ORC-002
for real instead of waiving it); retires the old blanket waiver for two
narrow named ones (ORC-003 for Review's one sanctioned api→rag crossing,
ORC-001 for Voice Conversation's 4-dependency Orchestration). Processing/
Aggregation get real scaffolding despite no current feature needing either.
Voice Conversation keeps its Pipecat TTS/LLM-unwrapped waiver — only
finishes the already-planned Stt/SessionLog/Prompt broker split (this
supersedes and absorbs the standalone split plan from the prior session;
the 6 dead orphan files from that attempt, confirmed NOT on the live call
path, are addressed by this rebuild's Voice Conversation wave). 9-wave
build order approved, Wave 1 (Session Lifecycle move + Processing/
Aggregation scaffolding) next — not started. Full record:
Projects/spanish-companion/decisions/six-layer-standard-rebuild.md.
New target-architecture canvas:
Projects/spanish-companion/six-layer-standard-rebuild.canvas.
CLAUDE.md is explicitly NOT yet updated — flagged as follow-up once code
lands.

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
