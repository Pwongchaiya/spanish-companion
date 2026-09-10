# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-10-0116.md
Researched current (Sep 2026) agent-workflow practice via a 4-lane parallel
fan-out (multi-agent orchestration, context engineering, loop engineering,
practitioner field reports), each lane required to cite live URLs tagged
[T1]/[T2] — synthesized to `decisions/agent-workflow-research-2026-09.md`.
Adopted two candidates into `.claude-toolkit/`: a deterministic `verify_gate.py`
Stop hook (blocks a "done" claim on failing tests) and `check_agent_models.py`
(enforces CLAUDE.md's Opus/Sonnet/Haiku tiering — caught 4 of 11 agents with
inverted tiers, all fixed). Also built `stall_ledger.py`: registers a
background agent's intent before dispatch so an HTTP 429 kill — which allows
no cleanup — still leaves a resumable record; sized directly against this
session's own earlier rate-limit incident. Toolkit suite: 106→132 passing.
No entities touched, no application code.
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
