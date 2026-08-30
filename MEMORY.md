# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-1654.md — Built and verified
all six waves of the Phase 3 rebuild plan via the Hierarchical Agent
Delegation convention (Opus plan/orchestrate this session, Sonnet streams
for judgment work, Haiku fan-out for 5 mechanical exception retargets).
Shared ApiError/RagError bases; every feature's exceptions named;
is_running() now captures the real subprocess return code; flag-write
failures no longer silent; ChunkRepositoryBroker/EmbeddingModelBroker
integration tests added; frontend start/stop/getStatus error handling +
rollback + vitest (8 tests); embedding-model mismatch warning + broker-
sourced version tagging + migration runbook; CLAUDE.md waiver table synced;
4 stray Phase 1 rag/ files deleted (user-approved). 123 backend tests +
frontend build/vitest green throughout. One real bug caught and fixed
during verification: a Voice Conversation fix's
`except subprocess.TimeoutExpired` referenced an unimported module and
would never have fired (pipecat 1.8.1 swallows its setup timeout
internally) — bounced back to the stream, fixed, re-verified.

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
