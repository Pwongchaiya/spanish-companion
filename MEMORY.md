# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-03-1422.md — Hackathon research
session, not layer-build work: extracted the Nerdy AI Hackathon Challenge's
full requirements via Playwright (homepage + /terms; no other pages exist)
and ground-truth-verified the repo's actual current state (not just re-read
from docs) by inspecting app.py imports/directory contents and running the
real test suites. Confirmed the six-layer rebuild genuinely is live in
app.py (old pre-rebuild directories are empty leftovers); found a live,
previously-unknown bug — record_practice returns 500 instead of 400 on a
missing JSON body (api/exposers/review.py:76) — and reproduced the 13
integration-test errors as a Windows port-exhaustion artifact, not an app
bug. Wrote a time-boxed plan of attack (competition summary → current-state
snapshot → judged-vs-unjudged gap list → Sep 3-18 plan) to
Projects/spanish-companion/decisions/hackathon-nerdy-plan-of-attack.md, with
two decisions explicitly left open for the user: whether the Phase 3/4
rebuild (Wave 8/9 below) pauses for hackathon prep or runs in parallel, and
whether the contest's IP-assignment term is acceptable. Six-layer rebuild
(Waves 1-7 of 9, landed 2026-09-02) and Wave 8/9 status unchanged this
session — see Projects/spanish-companion/decisions/six-layer-standard-rebuild.md
for that record.

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
