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
Voice Conversation, Ingestion, Retrieval, Generation, Review — split across
two top-level packages, `api` (Session Lifecycle, Voice Conversation,
Review) and `rag` (Ingestion, Retrieval, Generation), with `api` depending
on `rag` and never the reverse. Both packages are laid out layer-first,
then feature (`brokers/`, `models/`, `services/<feature>/`,
`controllers/<feature>/`). Retrieval internally uses a Strategy pattern for
hybrid search (dense now, lexical as a deferred seam). The frontend is being redesigned as React + TypeScript
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

**Phase 1 (historical — shipped code, not being retrofitted):**
- Voice pipeline (Steps 1-2): manual verification is primary — latency and
  conversational feel can't be unit tested. Log flags to file/console and
  inspect by hand before building anything on top.
- RAG (Step 3): a small `assert`-based smoke check that a known query
  ("preterite vs imperfect") returns the expected chunk — no framework,
  matches the scope doc's manual retrieval-quality check.
- Review Mode (Step 4+): unit tests for the flag-selection → retrieval →
  explanation flow are reasonable once the shape stabilizes; don't write them
  ahead of the code.

**Phase 2 (pytest, three tiers) — the standing rule for all new test code.**
Modeled on the user's `NL.Core.Entitlements` .NET project ("The Standard"
testing conventions); full detail in the decision record's "Resolved:
Phase 2 test strategy" section.
- **Unit** (`tests/unit/services|controllers/<feature>/`): every Broker
  mocked (`unittest.mock.Mock(spec=BrokerProtocol)`), split into
  `test_<method>_logic.py` / `_validation.py` / `_exceptions.py` per
  method, strict call-count verification on every mock touched,
  deterministic data only (no live `datetime.now()` or untracked
  randomness).
- **Integration** (`tests/integration/services/<feature>/`): real test
  Postgres, external APIs (Azure Speech, Gemini) mocked at the Broker
  boundary.
- **Acceptance** (`tests/acceptance/apis/<feature>/`): full Flask app
  in-process (`app.test_client()`), real test Postgres, external APIs
  mocked, self-cleaning HTTP round-trips (create → assert → delete).
- No new test dependencies — stdlib `unittest.mock` and plain `assert` on
  dataclasses cover everything Moq/FluentAssertions did in the reference
  project.

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

### Phase 2 Layer-Agent Mapping & Waivers

Full rationale, build order, and open-question resolution:
`Projects/spanish-companion/decisions/phase-2-agent-workflow.md` (Obsidian).
This section is the enforceable summary — every layer agent (Broker,
Foundation, Orchestration, Exposer, Auditor) reads CLAUDE.md automatically
and MUST apply these waivers without re-litigating them per invocation.

**Why waivers exist at all:** the `.claude-toolkit/` agent roster enforces
Hassan Habib's Standard six-layer rules (Broker → Foundation → Processing →
Orchestration → Aggregation → Exposer). This project's Phase 2 architecture
deliberately collapsed to three layers (Broker → Service → Controller,
see Architecture above). Run against the toolkit unmodified, 4 of 6
features fail the Auditor (Ingestion, Retrieval, Voice Conversation, Review
all have Services with 2+ broker/dependency counts — rejected by FND-003 /
ORC-001 / ORC-002). The mapping and waivers below resolve that mismatch.

**Layer-agent mapping:**

| Layer | Agent | Features | Waiver |
|---|---|---|---|
| Broker | Broker Agent | All six | None — SQLAlchemy + Alembic **adopted** (toolkit default kept, not waived). Output paths pinned per the `api`/`rag` layout, not the toolkit's `brokers/storage/` default. |
| Service, 1 broker | Foundation Agent | Session Lifecycle, Generation | Waive the 9-class default exception hierarchy — pin the actual exception list per feature at build time (this system only names one, `GenerationError`, in the whole architecture record) |
| Service, 2+ broker/deps | Orchestration Agent | Ingestion, Retrieval, Review | Waive ORC-001 (Florance dep-count limit) and ORC-002 (no direct broker deps) — this project has no Foundation layer beneath these, so direct broker deps are correct, not a violation |
| Processing | **Not used** | — | Its contract requires exactly one Foundation service beneath it; no such shape exists here |
| Aggregation | **Not used** | — | Its trigger is "Exposer needs >1 Orchestration service"; every controller here calls exactly one service |
| Controller, HTTP + in-process | Exposer Agent | Session Lifecycle, Review, Retrieval, Generation | Waive `/api/V1.0/` versioning (routes are unversioned: `/start`, `/stop`, `/status`, `/review*`); turn off React output (frontend is separately scaffolded in `frontend/`); for the two in-process controllers (`RetrievalController`, `GenerationController`) waive HTTP status-code mapping — there is no HTTP response to map |
| Controller, CLI/subprocess | **Hand-written, no agent** | Ingestion CLI, Voice Conversation `main()` | Not worth the waivers for ~20 lines of argparse/entrypoint code |
| Broker interfaces | — | All | `typing.Protocol`, not `ABC` — waive `python-adaptations-skill`'s ABC default and BRK-004 ("no local interface defined") |

**Voice Conversation: no agent, any layer.** Fully manual, supervised port
of Phase 1's `voice/bot.py`. Carries four hardware-verified fixes no agent
can discover or test (no agent has a microphone): echo suppression via
`AlwaysUserMuteStrategy`, the 44100/24000Hz sample-rate mismatch fix,
Windows SIGBREAK handling, periodic flag persistence. Gate on a manual
hardware/mic test, same method as Phase 1.

**Build order:** Session Lifecycle (full B/S/C loop, validates this waiver
approach cheaply) → shared broker wave, built once with both consumers'
method surfaces pinned up front (`ChunkRepositoryBroker`,
`EmbeddingModelBroker`, `GenerationBroker`, `FlagBroker`, `Flag` model,
`PracticeLogBroker`) → Ingestion / Retrieval / Generation in parallel →
Voice Conversation (manual, wall-clock parallel) → Review (depends on
Retrieval + Generation Controllers and the `Flag` model) → `app.py`
integration (factory, controller wiring, `/api/events` SSE, Origin/Referer
check, serve `frontend/dist` — owned by the main session, no single
feature/agent owns it) → frontend per feature.

**Status of these waivers is unverified until step 1 runs.** If the
Auditor Agent does not honor a CLAUDE.md-only waiver in practice, escalate
to a local `.claude/agents/*.md` patch (gitignored, machine-local, but
guaranteed to be read since it IS the agent's instructions) rather than
repeatedly overriding per-invocation.

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
