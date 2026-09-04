# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-03-2305.md — Session 5: fixed
two real bugs found while testing the J5 Docker build locally end-to-end
with Playwright (`ALLOWED_ORIGINS` missing port 10000, 403'ing every static
asset; embedding-model download hanging past gunicorn's 120s timeout —
fixed by baking the model into the image at build time with
`HF_HUB_DISABLE_XET=1`/`HF_HUB_OFFLINE=1`). Also committed pre-existing
uncommitted work (pg8000 URL-scheme normalization in
`chunk_repository_broker.py`). Committed: `77a115f`. Investigated (Planner
Agent, planning-only) adding browser-mic WebRTC voice chat to the public
deployment — found it needs a full transport rework (`aiortc`, per-connection
session model, net-new frontend/signaling), and the user ultimately put it
**on hold**: Render itself is no longer confirmed as the deploy host, and
separately, local Docker Desktop on Windows can't reach a real mic either
(no WSL2 host-audio passthrough). See
Projects/spanish-companion/decisions/voice-conversation-browser-webrtc-transport.md.
**Security note:** a real `GEMINI_API_KEY` value was printed into tool
output via an over-broad `docker inspect` — user may want to rotate it.
Render deployment itself still not done — no GitHub remote configured yet,
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
