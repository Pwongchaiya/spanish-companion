# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-2042.md — Completed the
source-of-truth fan-out: Voice Conversation (folder-layout only, hand-applied)
then Ingestion/Retrieval/Generation via true-parallel Hierarchical Agent
Delegation (Opus Plan/Orchestrate confirmed the wave's shape, then 3
concurrent background agents — Orchestration Agent x2, Foundation Agent x1
— built each feature, synthesized afterward). Ingestion: 3-tier exception
hierarchy matching Review's shape, new IngestionUnavailableError leaf.
Retrieval: 2-tier hierarchy; RetrievalUnavailableError now wraps into
RetrievalOrchestrationDependencyException before leaving retrieve() — the
central cross-feature coupling risk, required a coordinated fix to Review's
review_service_exceptions.py, verified live. Generation: folder layout +
one new GenerationServiceException safety net; GenerationError's
swallow-to-fallback behavior untouched. Synthesis-pass fixes after all three
agents landed: promoted inner_exception onto RagError (matching ApiError),
consolidated three independently-duplicated LoggingBroker shims into
rag/brokers/logging/, wired app.py to share its LoggingBroker with all four
services. 95 passed, 8 failed (Ingestion's pre-existing validation-test
punch list), 5 collection errors (4 pre-existing Review + 1 stray Phase 1
file) — no new breakage. All five features now rebuilt against source of
truth. See
Projects/spanish-companion/decisions/ingestion-retrieval-generation-rebuilt-against-source-of-truth.md
for the full citation-by-citation record. Next: the deferred test-writing
pass — not started.

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
