# CLAUDE.md — Spanish Learning Companion

> Primary context for Claude Code. Instantiated from
> `.claude-toolkit/.claude/templates/standard-claude-md-template.md` by `/project-init`,
> adapted for this project (see Architecture below). Update when architecture
> decisions change.

---

## Repository Overview

A voice-first Spanish conversation partner. The user talks to it like a friend;
the agent responds conversationally in real time. Errors are quietly flagged
during conversation (no interruption). After the conversation ends, the user
reviews flagged errors, picks one, and gets a grounded, sourced explanation
with a chance to practice the correction.

**Design principle driving every scope decision:** live conversation must stay
fast and natural — nothing expensive (RAG, verification) runs during
Conversation Mode. All grounding and correction work happens in the separate,
untimed Review Mode.

Full MVP scope, explicit out-of-scope list, and build order:
`spanish-companion-mvp-scope.md`.

The shared agent and skill toolkit lives at `.claude-toolkit/` as a git
submodule. All agents, skills, and slash commands are loaded from that path.

---

## Ask Before Building

Before generating any schema, table, or API contract, confirm the structure
with the user. Never invent field names, data types, or relationships.

---

## Tech Stack

| Concern | Technology |
|---|---|
| Voice orchestration | Pipecat (Python) |
| STT + TTS | Azure Speech |
| LLM | Gemini Flash-Lite — both conversation and RAG generation |
| Database | Postgres + pgvector |
| Embeddings | sentence-transformers, paraphrase-multilingual-MiniLM-L12-v2 (384-dim; BGE-small-en dropped — English-only, couldn't embed Spanish queries) |
| Corpus source | RAE grammar pages (MVP: 3-5 starter topics) |
| UI | Flask — minimal server, plain HTML/vanilla JS, no build tooling (Phase 1, shipped) |
| Config | python-dotenv — single `.env` at repo root |

**Phase 2 (planned, not yet built):** React + TypeScript, Vite static
build, Zustand, Server-Sent Events — replaces the plain HTML/vanilla JS UI
row above. Flask remains the server, now serving Vite's static output
instead of Jinja templates. See the Phase 2 decision record linked in
Architecture below.

---

## Architecture

**Phase 1 (Steps 0-5) shipped and was not entity/layer-based.** It did not
follow The Standard's Broker → Foundation → Processing → Orchestration →
Aggregation → Exposer build sequence — no CRUD entity registry, staged MVP
plan instead, tracked in `Projects/spanish-companion/state.md` (Pending
Work), mirrored from `spanish-companion-mvp-scope.md` Section 7:

1. Voice loop (Pipecat + Azure STT/TTS + Gemini), no flagging, no RAG.
2. Live error-flagging as a byproduct of the same generation call.
3. RAE corpus ingestion + dense-only retrieval (pgvector).
4. Review Mode v0: flagged list → selection → RAG-grounded explanation →
   single practice attempt.
5. Minimal UI over the above.

All five steps are done and verified end-to-end by the user via real
hardware/mic testing.

**Phase 2 (in design, not yet built) reverses this** — see the full
decision record: `Projects/spanish-companion/decisions/companion-architecture-broker-service-controller.md`.
Phase 2 adopts a simplified **Broker → Service → Controller** layering with
constructor-based dependency injection (`typing.Protocol` abstractions, no
DI framework), applied per-feature across six features: Session Lifecycle,
Voice Conversation, Ingestion, Retrieval, Generation, Review. Retrieval
internally uses a Strategy pattern for hybrid search (dense now, lexical as
a deferred seam). The frontend is being redesigned as React + TypeScript
(Vite static build, same-origin, no Next.js) with the same layering
expressed as hooks. Phase 1's code is not being patched — findings from a
four-agent Phase 1 review (code, design, security, live UI) feed Phase 2's
design directly instead of landing as fixes on the shipped code.

Two runtime modes (unchanged across both phases):
- **Conversation Mode** — real-time voice loop, no RAG calls, no spoken
  corrections.
- **Review Mode** — untimed, RAG-grounded explanation + single practice pass.

---

## Coding Standards

- Python 3.11+, full type hints.
- No `print()` for anything beyond quick local debugging during Steps 1-2 —
  replace with real logging once Review Mode (Step 4) exists.
- Black + Flake8 line length: 120.
- All knobs (model names, chunk size, top-k) from env config — no magic
  numbers hardcoded in pipeline code.

---

## Testing Standards

- Voice pipeline (Steps 1-2): manual verification is primary — latency and
  conversational feel can't be unit tested. Log flags to file/console and
  inspect by hand before building anything on top.
- RAG (Step 3): a small `assert`-based smoke check that a known query
  ("preterite vs imperfect") returns the expected chunk — no framework,
  matches the scope doc's manual retrieval-quality check.
- Review Mode (Step 4+): unit tests for the flag-selection → retrieval →
  explanation flow are reasonable once the shape stabilizes; don't write them
  ahead of the code.

---

## Git Workflow

- Feature branches off `main`. Conventional commits: `type: short description`.
- Never commit to `main` directly.
- Commit after every meaningful step, not one giant commit per MVP stage.

---

## Environment Variables

All secrets/config in `.env` at repo root. Never hardcode, never commit.
`.env.example` has placeholders.

| Variable | Purpose |
| --- | --- |
| `AZURE_SPEECH_KEY` | Azure Speech resource key (STT + TTS) |
| `AZURE_SPEECH_REGION` | Azure Speech resource region |
| `GEMINI_API_KEY` | Gemini API key (conversation + RAG generation) |
| `DATABASE_URL` | Postgres connection string (pgvector extension enabled) |

---

## Agent Coordination

Phase 1 had no Standard entity/layer build sequence (see Architecture).
Phase 2 does — entities will be registered via `/new-entity` once Phase 2
build work starts, using the Broker/Service/Controller layer agents against
the six features named in the Phase 2 decision record. The Planner Agent
owns session continuity via `/session-start` / `/session-end` in both
phases, reading and writing `Projects/spanish-companion/state.md`.

### Slash Commands

| Command | Purpose |
| --- | --- |
| `/session-start` | Planner reads Obsidian state and briefs on project status |
| `/session-end` | Syncs Obsidian state.md, sessions log, MEMORY.md |
| `/compact` | Context window management |

---

## Obsidian Vault

Vault path: `c:\Users\pwong\OneDrive\Documents\Obsidian\Notes`

### When to read

- At `/session-start`: read `Projects/spanish-companion/state.md` for current
  MVP stage and pending work.
- When a concept comes up, check `Projects/concepts/` before answering from
  training data.

### When to write

- At `/session-end`: save session summary to
  `Projects/spanish-companion/sessions/YYYY-MM-DD-HHmm.md`.
- When a new architectural decision is made (e.g. deviating from the scope
  doc's build order): create a note in `Projects/spanish-companion/decisions/`.

### Key vault files

| File | Purpose |
| --- | --- |
| `Projects/spanish-companion/state.md` | MVP stage tracker, pending work |
| `Projects/spanish-companion/sessions/` | Per-session summaries |
| `Projects/spanish-companion/decisions/` | Architectural decision records |

---

## Files to Ignore

- `.env` and any `*.env` file
- `data/corpus/` (raw fetched RAE pages)
- `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`
- `.claude/` (machine-specific symlinks + settings, not committed)
