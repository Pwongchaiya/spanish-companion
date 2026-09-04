# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-04-1224.md — Session 6: not
project feature work — a live diagnosis of how Claude communicates with
the user (ADHD-related), done via open-ended Q&A and a short roleplay.
Two durable rules written to the **global** `~/.claude/CLAUDE.md` (not
this project's CLAUDE.md, applies everywhere): (1) Communication style
rewritten — root cause is signal-to-noise, not reply length (user reads
the whole reply but loses the answer inside supporting detail, and a
single reply is itself fatiguing to read) — new rule is an ~8-line cap,
one-thing-at-a-time pacing, concrete-before-abstract, structure over
prose. (2) New "Correction compliance" section — separate trigger found
from past Broker→Service→Controller sessions: Claude built without
confirming naming/architecture/task understanding, deviated from set
rules, then pushed back on direct corrections most of the time with
justification text — new rule is immediate compliance with a direct
correction, no pushback, except genuine safety/destructive-action
conflicts. No spanish-companion repo files touched; nothing committed to
this repo this session. Pending items from session 5 (J5 Render deploy,
RAG explanation quality gap, `.env.docker` cleanup, Gemini key rotation,
Wave 9 pytest+CLAUDE.md sync) are all unchanged — see state.md.

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
