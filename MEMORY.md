# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-02-0934.md — Executed the
six-layer Standard rebuild approved 2026-08-30: Waves 1-7 of 9 landed as
10 commits (2f04281..6a9c2ac on feat/pwongchaiya/step0-repo-scaffold) via
the Hierarchical Agent Delegation convention. Session Lifecycle moved to
services/foundations/; ChunkRepositoryService/EmbeddingModelService built
as new shared Foundations under Ingestion+Retrieval; IngestionService/
HybridRetrievalService rewired onto them (IngestionUnavailableError/
RetrievalUnavailableError retired); GenerationService moved to Foundation
tier, its pass-through GenerationController deleted; FlagService/
PracticeLogService built as new Foundations under Review, absorbing
ReviewOrchestrator logic verbatim; ReviewOrchestrator fully rebuilt onto
all four service deps directly (RetrievalController/GenerationController
both gone from that call path); every Controller renamed/moved to
exposers/ (or deleted where it was a pure pass-through — RetrievalController,
GenerationController); a real bug fixed along the way (Review's exception-
wrap-depth isinstance check was silently returning 400 instead of 404 for
every not-found flag). app.py composition root rewired to match, verified
with a real create_app() boot and a live smoke test that round-trips a 404
through the full stack end to end. Two Orchestration Agent dispatches hit
a weekly rate limit mid-task and were resumed via cross-agent messaging
rather than restarted. Wave 8 (Voice Conversation, hand-written,
hardware-gated) and Wave 9 (pytest, user's job) deliberately not started
this session. CLAUDE.md's Architecture section and waiver table are now
stale (still describe the retired 3-layer pattern) — flagged to the user
at session-end, not yet approved/applied. Full record:
Projects/spanish-companion/decisions/six-layer-standard-rebuild.md.

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
