# CLAUDE.md — Spanish Learning Companion

> Primary context for Claude Code. Instantiated from
> `.claude-toolkit/.claude/templates/standard-claude-md-template.md` by `/project-init`,
> adapted for this project (see Architecture below). Update when architecture
> decisions change.

---

## Repository Overview

A voice-first Spanish conversation partner. The user talks to it like a friend; the agent responds conversationally in real time. Errors are quietly flagged during conversation (no interruption). After the conversation ends, the user reviews flagged errors, picks one, and gets a grounded, sourced explanation with a chance to practice the correction.

**Design principle driving every scope decision:** 
live conversation must stay fast and natural — nothing expensive (RAG, verification) runs during Conversation Mode. All grounding and correction work happens in the separate,untimed Review Mode.

Full MVP scope, explicit out-of-scope list, and build order:
`spanish-companion-mvp-scope.md`.

The shared agent and skill toolkit lives at `.claude-toolkit/` as a git
submodule. All agents, skills, and slash commands are loaded from that path.

---

## Ask Before Building

Before generating any schema, table, or API contract, confirm the structure with the user. Never invent field names, data types, or relationships.

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
Phase 2 adopts a simplified **Broker → Service → Controller** layering with constructor-based dependency injection (`typing.Protocol` abstractions, no DI framework), applied per-feature across six features: Session Lifecycle, Voice Conversation, Ingestion, Retrieval, Generation, Review — split across two top-level packages, `api` (Session Lifecycle, Voice Conversation, Review) and `rag` (Ingestion, Retrieval, Generation), with `api` depending on `rag` and never the reverse. Both packages are laid out layer-first, then feature (`brokers/`, `models/`, `services/<feature>/`, `controllers/<feature>/`). Retrieval internally uses a Strategy pattern for hybrid search (dense now, lexical as a deferred seam). The frontend is being redesigned as React + TypeScript
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
  explanation flow are reasonable once the shape stabilizes; don't write them ahead of the code.

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

**Scripts, hooks, and one-off tooling** are covered by the global "Leave one
runnable check" rule in `~/.claude/CLAUDE.md`, not by the three tiers above —
an `assert`-based `__main__` self-check, written in the same turn as the code.
The tiers apply to `api/` and `rag/` production code only.

**Frontend (vitest + @testing-library/react, added Phase 3).** Pairs with the
already-installed Vite, no new build tooling. Scope deliberately minimal —
covers newly-fixed logic (e.g. `useSessionState.ts`'s start/stop/getStatus
success, failure-with-rollback, and error-surfaced paths), not a
full-coverage push across the frontend. `npm test` (alias for `vitest`) from
`frontend/`.

---

## Git Workflow

- Feature branches off `main`. Conventional commits: `type: short description`.
- Never commit to `main` directly.
- Commit after every meaningful step, not one giant commit per MVP stage.

---

## Environment Variables

All secrets/config in `.env` at repo root. Never hardcode, never commit.
`.env.example` has placeholders.

**Claude must never edit `.env` directly — non-negotiable.** If a change
requires updating `.env` (e.g. a config key rename, a connection-string
scheme change), update `.env.example` and tell the user what to change in
their own `.env`; let them make the edit themselves.

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
build work starts, using the Broker/Service/Controller layer agents against the six features named in the Phase 2 decision record. The Planner Agent
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

**Naming/structure must be verified against the actual `NL.Core.Users` `.cs`
file** (`C:/Users/pwong/source/repos/NL.Core.Users`) — not a sibling entity's
Python file, not a third-party snippet. "Mirrors X's shape" is not a
citation unless X is the real `.cs` file, with a file:line. See
[[Projects/spanish-companion/decisions/mistake-pattern-source-of-truth-conformance|decision record]]
for why this rule exists.

**Layer-agent mapping:**

| Layer | Agent | Features | Waiver |
|---|---|---|---|
| Broker | Broker Agent | All six | None — SQLAlchemy + Alembic **adopted** (toolkit default kept, not waived). Output paths pinned per the `api`/`rag` layout, not the toolkit's `brokers/storage/` default. |
| Service, 1 broker | Foundation Agent | Session Lifecycle, Generation | Waive the 9-class default exception hierarchy — pin the actual exception list per feature, verified non-empty for every feature that can fail in more than one way. Verified against source-of-truth: Session Lifecycle names 4, Generation names 2 — all inherit `ApiError`/`RagError`. See [[Projects/spanish-companion/decisions/session-lifecycle-rebuilt-against-source-of-truth\|Session Lifecycle]] and [[Projects/spanish-companion/decisions/ingestion-retrieval-generation-rebuilt-against-source-of-truth\|Ingestion/Retrieval/Generation]] records. |
| Service, 2+ broker/deps | Orchestration Agent | Ingestion, Retrieval, Review | Waive ORC-001 (Florance dep-count limit) and ORC-002 (no direct broker deps) — no Foundation layer beneath these, so direct broker deps are correct. Verified against source-of-truth: Ingestion names 5, Retrieval names 3 (no Validation tier — `retrieve()`'s only input check is a bare `ValueError`), Review names 6 across 3 wrapper tiers. Retrieval's leaf reaches Review pre-wrapped as `RetrievalOrchestrationDependencyException`. See [[Projects/spanish-companion/decisions/review-rebuilt-against-source-of-truth\|Review]] and [[Projects/spanish-companion/decisions/ingestion-retrieval-generation-rebuilt-against-source-of-truth\|Ingestion/Retrieval/Generation]] records. |
| Processing | Processing Agent (new entities only, from 2026-09-10) | Per-entity, wherever higher-order logic (upsert, computed occurrence counts, status transitions) sits on top of a single Foundation service | **Reversed project-wide 2026-09-10** — the original "Not used" waiver collapsed Processing into Foundation/Service, which pushed upsert-style logic into what should be a pure CRUD tier (get/put/delete/create/getall only). Going forward, Foundation stays low-level-only; Processing owns higher-order logic on top of it, matching Standard's philosophy. **Not retroactive** — the 5 already-shipped features (Session Lifecycle, Generation, Ingestion, Retrieval, Review) keep their existing 3-layer shape; this applies starting with the LearnerProfile entity cluster's re-split into 3 entities (LearnerProfile, MistakePattern, TopicCovered), each getting its own Broker → Foundation → Processing sequence where it needs one. |
| Aggregation | **Not used** | — | Its trigger is "Exposer needs >1 Orchestration service"; every controller here calls exactly one service |
| Controller, HTTP + in-process | Exposer Agent | Session Lifecycle, Review, Retrieval, Generation | Waive `/api/V1.0/` versioning (routes are unversioned: `/start`, `/stop`, `/status`, `/review*`); turn off React output (frontend is separately scaffolded in `frontend/`); for the two in-process controllers (`RetrievalController`, `GenerationController`) waive HTTP status-code mapping — there is no HTTP response to map |
| Controller, CLI/subprocess | **Hand-written, no agent** | Ingestion CLI, Voice Conversation `main()` | Not worth the waivers for ~20 lines of argparse/entrypoint code |
| Broker interfaces | — | All | `typing.Protocol`, not `ABC` — waive `python-adaptations-skill`'s ABC default and BRK-004 ("no local interface defined"). Reframed post-audit: this doesn't diverge from the reference `NL.Core.Entitlements` project, it matches it — `IEntitlementService.cs` sits next to `EntitlementService.cs` there too, interfaces co-located with implementation. The toolkit's ABC/BRK-004 default is the outlier, not this waiver ([[Projects/spanish-companion/decisions/phase-2-vs-reference-architecture-audit\|F18]]) |

**Voice Conversation: no agent, any layer.** Fully manual, supervised port
of Phase 1's `voice/bot.py`. Carries four hardware-verified fixes no agent
can discover or test (no agent has a microphone): echo suppression via
`AlwaysUserMuteStrategy`, the 44100/24000Hz sample-rate mismatch fix,
Windows SIGBREAK handling, periodic flag persistence. Gate on a manual
hardware/mic test, same method as Phase 1.

**Voice Conversation exceptions** (both `ApiError`): `VoiceConversationConfigError`
(missing/invalid Azure Speech or Gemini credentials, audio device setup) and
`VoiceConversationPipelineError` (audio device init failure, unrecoverable
Gemini failure after retry).

**Known gap, deliberately unclosed:** pipeline setup exceeding its 60s
timeout can't be caught today — pipecat 1.8.1's `PipelineWorker` swallows
its own setup timeout internally and never raises. Closing it needs
`@worker.event_handler("on_setup_timeout")` raising `VoiceConversationPipelineError`
— left as a `ponytail:` comment at the call site, not a try/except that'd
never fire. `SubprocessBotProcessBroker` exposes the subprocess's return
code (`get_last_return_code()`) so `ConversationSessionService.get_status()`
can distinguish a crash from a graceful stop. See
[[Projects/spanish-companion/decisions/phase-2-vs-reference-architecture-audit|F20-F22]].

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

### Hierarchical Agent Delegation

A general convention for any multi-step work that splits into judgment work plus
bounded mechanical work at meaningful scale (roughly 3+ independent, parallelizable
sub-tasks) — not limited to Standard layer builds. Established from the audit +
Phase 3 planning pipeline that produced
`decisions/phase-3-architectural-foundation-rebuild.md`. Full rationale and worked
example: `Projects/spanish-companion/decisions/hierarchical-agent-delegation.md`
(Obsidian).

| Tier | Model | Role | Use for |
|---|---|---|---|
| Plan/Orchestrate | Opus | Task decomposition, wave/dependency ordering, synthesizing parallel worker output, verification-bounce decisions | Any judgment call needing the whole picture — no single worker sees the full dependency graph |
| Audit/Build | Sonnet | The existing Broker/Foundation/Processing/Orchestration/Aggregation/Exposer Agents, and the Auditor Agent | Unchanged from current practice — actual code generation and Standard-rule checking |
| Worker | Haiku | Bounded, mechanical, no-judgment sub-tasks against a fully self-contained input | Parallel fan-out extraction/transformation — each sub-task independent, no synthesis required |

**Verification-bounce protocol** (mirrors the existing Auditor Agent convention): a Plan/Orchestrate-tier pass checks Worker or Audit/Build output against its source input before accepting it. On failure, bounce back to the originating tier for correction — cap at 3 cycles, then escalate to the user rather than looping indefinitely.

**Do not apply this for its own sake.** A single bug fix, a small sequential task, or
work with no natural judgment/mechanical split doesn't need tiering — dispatch
directly.

**Model tiering is enforced, not advisory.** `.claude-toolkit/checks/check_agent_models.py`
fails if an agent's `model:` frontmatter drifts from its tier, or if a new agent
isn't listed. Four of eleven agents had silently inverted tiers before this landed
(2026-09-10). When dispatching ad-hoc subagents, pass the tier's model explicitly —
a fan-out that defaults to Opus is how this project exhausted a session limit.

**Register every background dispatch before launching it.** An agent killed by an
HTTP 429 cannot run cleanup, so the record has to exist beforehand:

```bash
python .claude-toolkit/scripts/stall_ledger.py register --vault "$VAULT" --project spanish-companion --id <id> --label "<what it is>"
python .claude-toolkit/scripts/stall_ledger.py done     --vault "$VAULT" --project spanish-companion --id <id>
python .claude-toolkit/scripts/stall_ledger.py stalled  --vault "$VAULT" --project spanish-companion --id <id> --reset "<reset text from the 429>"
```

`SessionStart` reports anything left standing. Resume is a decision — confirm with
the user before relaunching stalled work, even once the limit has reset.

### Slash Commands

| Command | Purpose |
| --- | --- |
| `/session-start` | Planner reads Obsidian state and briefs on project status |
| `/session-end` | Syncs Obsidian state.md, sessions log, MEMORY.md |
| `/compact` | Context window management |

---

## Codebase Documentation (repowise)

Repo-level MCP indexer (`mcp__repowise__*` tools) — architecture overviews,
contextual docs on files/symbols, change-risk assessment, dead-code
detection, semantic search. Index is per-repo and does **not** auto-update
on commit.

### When to use

- "How does X relate to Y" / architecture-overview questions →
  `get_overview` / `get_context` before manually reading multiple files
- Symbol lookup or "why does this exist" → `get_symbol` / `get_why`
- Assessing blast radius of a change → `get_change_risk` / `get_risk`
- Free-text/semantic questions across the codebase → `search_codebase` /
  `get_answer`
- Finding unused code → `get_dead_code`

### When not to

- Exact string/pattern search → `Grep`, not repowise (repowise is
  semantic, not literal)
- A file whose path is already known → `Read` directly
- Anything touching code changed very recently — check the SessionStart
  staleness warning first; if the index is behind HEAD, verify repowise's
  answer against the live file before trusting it (see Phase 3's "verify
  against actual current code, not stale docs" rule above — the same
  applies to a stale index)

### Keeping it current

If a SessionStart hook reports the index is behind HEAD, tell the user to
run `repowise update` — never run it yourself.

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
- `.claude/` (machine-specific settings, not committed — `commands/`/`agents/`
  are synced copies of `.claude-toolkit/.claude/{commands,agents}`, not
  symlinks: this repo lives under OneDrive, which re-materializes NTFS
  symlinks as independent copies, so a `SessionStart` hook runs
  `.claude-toolkit/scripts/sync_commands.py` to keep them current instead)
