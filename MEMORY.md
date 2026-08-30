# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-29-1837.md — Rebuilt Session
Lifecycle's Broker/Foundation/Controller layer against the source-of-truth
repo NL.Core.Entitlements, file:line cited for every structural choice, in
two passes: (1) error handling — ApiError gained inner_exception, leaf
exceptions renamed and now always wrapped into SessionValidationException/
SessionServiceException before leaving the service, new LoggingBroker,
controller HTTP remap (not-running now 404, was 409); (2) folder layout —
brokers/services/models restructured into per-feature subpackages matching
the reference tree (controllers stay flat, matching source). Corrected 3
`.claude-toolkit` skills that disagreed with the actual reference project,
landed as a separate submodule commit. Full backend suite (123 tests) green
throughout. See
Projects/spanish-companion/decisions/session-lifecycle-rebuilt-against-source-of-truth.md
for the full citation-by-citation record. Next: same rebuild for the
remaining five features (fan-out) — not started.

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
