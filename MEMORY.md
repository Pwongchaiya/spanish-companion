# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-03-2153.md — Tri-Nature Gate
follow-up 3 (deployment/API security hardening) resolved and built: a
Brainstorm Agent design pass found the real risk on a public deploy isn't
auth/rate-limiting/CORS (the follow-up's own framing) but attack-surface
reduction — `POST /start` spawns a subprocess and spends API credit,
`/api/events` is an unbounded SSE stream. Built via `/hierarchical-delegation`
(2 waves, 4 general-purpose agents): `api/app_public.py` (stripped
Review-only entrypoint, never registers Session Lifecycle or `/api/events`),
`ReviewOrchestrator.explain_flag` cached (`lru_cache` — flags immutable,
corpus static, so cost is bounded after first use per flag), a
`VITE_PUBLIC_MODE` frontend build variant, a seeded `data/demo_flags.json`,
and a multi-stage `Dockerfile` for Render (confirmed against Render's actual
docs — native runtimes can't mix Node+Python, Docker is the documented
path). No auth for the deploy: declined, not deferred, same reasoning as
the Gate's own refusal. Also fixed a real, independent bug: the Origin
check's `startswith()` prefix match let `http://localhost:5000.evil.com`
bypass it — now exact scheme+host matching. 139/139 unit tests pass.
Committed: `2d57f5c`. See
Projects/spanish-companion/decisions/deployment-api-security-hardening.md
(includes a 9-step deploy runbook). Render deployment itself not yet done —
hard cutoff 6pm 2026-09-10.

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
