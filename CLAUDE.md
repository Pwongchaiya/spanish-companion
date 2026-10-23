# CLAUDE.md — Spanish Learning Companion

> Primary context for Claude Code. Made from
> the `standard` plugin's `.claude/templates/standard-claude-md-template.md` via `/project-init`,
> adapted this project (see Architecture below). Update when architecture
> decisions change.

---

## Repository Overview

Voice-first Spanish conversation partner. User talk to it like friend; agent respond real time, conversational. Errors flag quiet during talk, no interrupt. After talk end, user review flagged errors, pick one, get grounded sourced explain, chance practice correction.

**Design principle drive every scope decision:** 
live talk must stay fast, natural — nothing expensive (RAG, verify) run during Conversation Mode. All ground and correction work happen in separate, untimed Review Mode.

Full scope, out-of-scope list, build order:
`spanish-companion-mvp-scope.md` (filename kept for history; project is past MVP stage).

Shared agent, skill toolkit is the `standard` Claude Code plugin (marketplace
`pwongchaiya-toolkit`, local clone `~/.claude/plugins/marketplaces/pwongchaiya-toolkit/`). All agents, skills, slash
commands, hooks load from the plugin (`standard:` prefix). Scripts below are
run from that stable clone path — the plugin cache path changes per version.

---

## Ask Before Building

Before make any schema, table, or API contract, confirm structure with user. Never invent field names, data types, relationships.

---

## Tech Stack

| Concern | Technology |
|---|---|
| Voice orchestration | Pipecat (Python) |
| STT + TTS | Azure Speech |
| LLM | Gemini Flash-Lite — both talk + RAG generate |
| Database | Postgres + pgvector |
| Embeddings | sentence-transformers, paraphrase-multilingual-MiniLM-L12-v2 (384-dim; BGE-small-en drop — English-only, no embed Spanish query) |
| Corpus source | RAE grammar pages (initial: 3-5 start topic) |
| UI | Flask — minimal server, plain HTML/vanilla JS, no build tool (Phase 1, shipped) |
| Config | python-dotenv — single `.env` at repo root |

**UI now:** React + TypeScript, Vite static build (`frontend/`), serve
by Flask instead of Jinja templates. Replace Phase 1 plain
HTML/vanilla JS row above.

---

## Architecture

**Phase 1 (Steps 0-5) shipped, not entity/layer-based.** Not follow
The Standard's Broker → Foundation → Processing → Orchestration →
Aggregation → Exposer build sequence — no CRUD entity registry, staged
plan instead, track in `Projects/spanish-companion/state.md` (Pending
Work), mirror from `spanish-companion-mvp-scope.md` Section 7:

1. Voice loop (Pipecat + Azure STT/TTS + Gemini), no flag, no RAG.
2. Live error-flag as byproduct of same generate call.
3. RAE corpus ingest + dense-only retrieve (pgvector).
4. Review Mode v0: flag list →
   pick → RAG-ground explain →
   single practice try.
5. Minimal UI over above.

All five step done, verify end-to-end by user via real
hardware/mic test.

**Now: full Standard six-layer pattern** (Broker → Foundation →
Processing → Orchestration → Aggregation → Exposer), across six feature
(Session Lifecycle, Voice Conversation, Ingestion, Retrieval, Generation,
Review) split two package — `api` (Session Lifecycle, Voice
Conversation, Review) and `rag` (Ingestion, Retrieval, Generation), `api`
depend on `rag`, never reverse. Layer-first then feature layout
(`brokers/`, `models/`, `services/<feature>/`, `controllers/<feature>/`).
Retrieval use Strategy pattern for hybrid search (dense now, lexical
defer seam). Frontend: React/TS hooks mirror layering.

Old history: Phase 2 first use collapsed three-layer
Broker → Service → Controller shape (see
`decisions/companion-architecture-broker-service-controller.md`); Wave
1-8 of 9-wave rebuild (2026-09-03) replace it per-feature with the
six-layer pattern above. See `state.md` Entity Registry for per-layer
status, and "Phase 2 Layer-Agent Mapping & Waivers" below for the
per-feature waiver rebuild need. Don't build against old
three-layer shape.

Two runtime mode (same both phase):
- **Conversation Mode** — real-time voice loop, no RAG call, no spoken
  correction.
- **Review Mode** — untimed, RAG-ground explain + single practice pass.

---

## Coding Standards

- Python 3.11+, full type hint.
- No `print()` for anything beyond quick local debug during Steps 1-2 —
  swap for real logging once Review Mode (Step 4) exist.
- Black + Flake8 line length: 120.
- All knob (model name, chunk size, top-k) from env config — no magic
  number hardcode in pipeline code.

---

## Testing Standards

**Phase 1 (old, not retrofit):** manual verify for voice
pipeline (latency/feel not unit-testable), one `assert`-based smoke
check for RAG retrieve quality. Replace by tier below for all
new code.

**Standing rule all new test code — pytest, three tier.**
Model on user's `NL.Core.Users` .NET project (`C:/Users/pwong/source/repos/NL.Core.Users` — wins over `NL.Core.Entitlements` on any conflict) ("The Standard"
test convention); full detail in decision record's "Resolved:
Phase 2 test strategy" section.
- **Unit** (`tests/unit/services|controllers/<feature>/`): every Broker
  mock (`unittest.mock.Mock(spec=BrokerProtocol)`), split into
  `test_<method>_logic.py` / `_validation.py` / `_exceptions.py` per
  method, strict call-count verify on every mock touch,
  deterministic data only (no live `datetime.now()` or untrack
  random).
- **Integration** (`tests/integration/services/<feature>/`): real test
  Postgres, external API (Azure Speech, Gemini) mock at Broker
  boundary.
- **Acceptance** (`tests/acceptance/apis/<feature>/`): full Flask app
  in-process (`app.test_client()`), real test Postgres, external API
  mock, self-clean HTTP round-trip (create → assert → delete).
- No new test dependency — stdlib `unittest.mock` and plain `assert` on
  dataclass cover everything Moq/FluentAssertions did in reference
  project.

**Script, hook, one-off tool** cover by global "Leave one
runnable check" rule in `~/.claude/CLAUDE.md`, not by three tier above —
`assert`-based `__main__` self-check, write same turn as code.
Tier apply `api/` and `rag/` production code only.

**Frontend (vitest + @testing-library/react, add Phase 3).** Pair with the
already-install Vite, no new build tool. Scope deliberate minimal —
cover newly-fix logic (e.g. `useSessionState.ts`'s start/stop/getStatus
success, failure-with-rollback, error-surface path), not
full-coverage push across frontend. `npm test` (alias for `vitest`) from
`frontend/`.

---

## Git Workflow

- Feature branch off `main`. Conventional commit: `type: short description`.
- Never commit to `main` direct.
- Commit after every meaningful step, not one giant commit per build stage.

---

## Environment Variables

All secret/config in `.env` at repo root. Never hardcode, never commit.
`.env.example` have placeholder.

**Claude must never edit `.env` direct — non-negotiable.** If change
need update `.env` (e.g. config key rename, connection-string
scheme change), update `.env.example` and tell user what change in
own `.env`; let them make the edit themselves.

| Variable | Purpose |
| --- | --- |
| `AZURE_SPEECH_KEY` | Azure Speech resource key (STT + TTS) |
| `AZURE_SPEECH_REGION` | Azure Speech resource region |
| `GEMINI_API_KEY` | Gemini API key (talk + RAG generate) |
| `DATABASE_URL` | Postgres connect string (pgvector extension on) |

---

## Agent Coordination

Phase 1 had no Standard entity/layer build sequence (see Architecture).
Phase 2 do — entity register via `/new-entity` once Phase 2
build work start, use Broker/Service/Controller layer agent against six feature name in Phase 2 decision record. Planner Agent
own session continuity via `/session-start` / `/session-end` both
phase, read/write `Projects/spanish-companion/state.md`.

### Phase 2 Layer-Agent Mapping & Waivers

Full rationale, build order, open-question resolve:
`Projects/spanish-companion/decisions/phase-2-agent-workflow.md` (Obsidian).
This section the enforceable summary — every layer agent (Broker,
Foundation, Orchestration, Exposer, Auditor) read CLAUDE.md auto
and MUST apply waiver without re-argue per call.

**Why waiver exist:** the `standard` plugin's agent roster enforce
Hassan Habib's Standard six-layer rule (Broker → Foundation → Processing →
Orchestration → Aggregation → Exposer). This project's original Phase 2
architecture collapse to three layer (Broker → Service → Controller) —
since replaced by six-layer rebuild (see Architecture above); waivers below
cover what six-layer shape still diverge on. Under old three-layer shape, 4 of 6
feature fail Auditor (Ingestion, Retrieval, Voice Conversation, Review
all have Service with 2+ broker/dependency count — reject by FND-003 /
ORC-001 / ORC-002). Mapping and waiver below fix that mismatch.

**Naming/structure must be verify against actual `NL.Core.Users` `.cs`
file** (`C:/Users/pwong/source/repos/NL.Core.Users`) — not sibling entity's
Python file, not third-party snippet. "Mirrors X's shape" not
citation unless X the real `.cs` file, with file:line. See
[[Projects/spanish-companion/decisions/mistake-pattern-source-of-truth-conformance|decision record]]
for why rule exist.

**Layer-agent mapping:**

| Layer | Agent | Features | Waiver |
|---|---|---|---|
| Broker | Broker Agent | All six | None — SQLAlchemy + Alembic **adopted** (toolkit default kept, not waived). Output path pin per `api`/`rag` layout, not toolkit's `brokers/storage/` default. |
| Service, 1 broker | Foundation Agent | Session Lifecycle, Generation | Waive 9-class default exception hierarchy — pin actual exception list per feature, verified non-empty for every feature that can fail more than one way. Verified against source-of-truth: Session Lifecycle names 4, Generation names 2 — all inherit `ApiError`/`RagError`. See [[Projects/spanish-companion/decisions/session-lifecycle-rebuilt-against-source-of-truth\|Session Lifecycle]] and [[Projects/spanish-companion/decisions/ingestion-retrieval-generation-rebuilt-against-source-of-truth\|Ingestion/Retrieval/Generation]] records. |
| Service, 2+ broker/deps | Orchestration Agent | Ingestion, Retrieval, Review, LearnerProfile | Waive ORC-001 (Florance dep-count limit; LearnerProfile's orchestrator takes 5 Foundation/Processing deps — `learner_profile_orchestration_service.py:71-82`). ORC-002 (no direct broker deps) waiver **stale as of six-layer rebuild** — verified 2026-09-11 against actual constructors: `IngestionOrchestrationService.__init__` (`rag/services/orchestrations/ingestion/ingestion_service.py:89-95`) takes `chunk_repository_service`/`embedding_model_service` (both Foundation), `RetrievalOrchestrationService.__init__` (`rag/services/orchestrations/retrieval/retrieval_service.py:75-84`) takes `embedding_model_service` (Foundation) + strategy objects, `ReviewOrchestrationService.__init__` (`api/services/orchestrations/review/review_service.py:86-102`) takes `flag_service`/`practice_log_service`/`generation_service` (Foundation) + `retrieval_service` (another Orchestration) + six LearnerProfile-cluster/session deps (`learner_profile_processing_service`, `mistake_pattern_processing_service`, `session_log_entry_service`, `live_transcript_service`, `ingestion_queue_processing_service`, `topic_covered_processing_service`). None hold direct business-broker dependency — only `logging_broker`/`configuration_broker`, cross-cutting and exempt under Standard regardless. ORC-002 no longer need waive for any of three; keep only ORC-001 dep-count waiver. Verified against source-of-truth: Ingestion names 5, Retrieval names 3 (no Validation tier — `retrieve()`'s only input check bare `ValueError`), Review names 6 across 3 wrapper tiers. Retrieval's leaf reaches Review pre-wrapped as `RetrievalOrchestrationDependencyException`. See [[Projects/spanish-companion/decisions/review-rebuilt-against-source-of-truth\|Review]] and [[Projects/spanish-companion/decisions/ingestion-retrieval-generation-rebuilt-against-source-of-truth\|Ingestion/Retrieval/Generation]] records. |
| Processing | Processing Agent (new entities only, from 2026-09-10) | Per-entity, wherever higher-order logic (upsert, computed occurrence counts, status transitions) sits on top of a single Foundation service | **Reversed project-wide 2026-09-10** — original "Not used" waiver collapsed Processing into Foundation/Service, which pushed upsert-style logic into what should be pure CRUD tier (get/put/delete/create/getall only). Going forward, Foundation stay low-level-only; Processing owns higher-order logic on top, matching Standard's philosophy. **Not retroactive** — 5 already-shipped features (Session Lifecycle, Generation, Ingestion, Retrieval, Review) keep existing 3-layer shape; this applies starting with LearnerProfile entity cluster's re-split into 3 entities (LearnerProfile, MistakePattern, TopicCovered), each getting own Broker → Foundation → Processing sequence where it needs one. |
| Aggregation | Aggregation Agent | Session Recap (`api/services/aggregations/session_recap/`) | None. Used once: `GET /progress/recap` composes Review's `list_flags()` and Progress's `get_latest_completed_session()`, meeting the trigger "Exposer needs >1 Orchestration service". Every other controller still calls exactly one service. |
| Controller, HTTP + in-process | Exposer Agent | Session Lifecycle, Review, LearnerProfile | Waive `/api/V1.0/` versioning (routes unversioned: `/start`, `/stop`, `/status`, `/review*`); turn off React output (frontend separately scaffolded in `frontend/`). `RetrievalController`/`GenerationController` were deleted (`fcf743a`) as valueless pass-throughs with a single caller each — Review now depends on Retrieval/Generation's own services directly. `LearnerProfileController` (`api/exposers/learner_profile.py`) kept despite that precedent because it has two eventual callers (`voice_conversation.py`, `review.py`); waives HTTP status-code mapping — no HTTP response to map |
| Controller, CLI/subprocess | **Hand-written, no agent** | Ingestion CLI, Voice Conversation `main()` | Not worth waiver for ~20 lines of argparse/entrypoint code |
| Broker interfaces | — | All | `typing.Protocol`, not `ABC` — waive `python-adaptations-skill`'s ABC default and BRK-004 ("no local interface defined"). Reframed post-audit: this doesn't diverge from reference `NL.Core.Users` project, it matches it — `IUserProfileService.cs` sits next to `UserProfileService.cs` in `NL.Core.Users.Api/Services/Foundations/UserProfiles/`, interfaces co-located with implementation. Toolkit's ABC/BRK-004 default the outlier, not this waiver ([[Projects/spanish-companion/decisions/phase-2-vs-reference-architecture-audit\|F18]]) |

**Voice Conversation: no agent, any layer.** Full manual, supervised port
of Phase 1's `voice/bot.py`. Carries three hardware-verified fixes no agent
can discover or test (no agent has microphone): echo suppression via
`AlwaysUserMuteStrategy`, the 44100/24000Hz sample-rate mismatch fix,
periodic flag persistence. Graceful `/stop` uses a polled stop-flag file
(`_watch_for_stop_signal`), not Phase 1's Windows SIGBREAK port — that
mechanism was confirmed broken via isolated repro, 2026-08-29. Gate on
manual hardware/mic test, same method as Phase 1.

**Voice Conversation exceptions** (both `ApiError`): `VoiceConversationConfigError`
(missing/invalid Azure Speech or Gemini credentials, audio device setup) and
`VoiceConversationPipelineError` (audio device init failure, unrecoverable
Gemini failure after retry).

**Known gap, deliberately unclosed:** pipeline setup exceeding 60s
timeout can't be caught today — pipecat 1.8.1's `PipelineWorker` swallows
own setup timeout internally and never raises. Closing it needs
`@worker.event_handler("on_setup_timeout")` raising `VoiceConversationPipelineError`
— left as a `ponytail:` comment at the call site, not a try/except that'd
never fire. `SubprocessBotProcessBroker` exposes subprocess's return
code (`get_last_return_code()`) so `ConversationSessionService.get_status()`
can distinguish crash from graceful stop. See
[[Projects/spanish-companion/decisions/phase-2-vs-reference-architecture-audit|F20-F22]].

**Build order:** Session Lifecycle (full B/S/C loop, validates this waiver
approach cheaply) → shared broker wave, built once with both consumers'
method surfaces pinned up front (`ChunkRepositoryBroker`,
`EmbeddingModelBroker`, `GenerationBroker`, `FlagBroker`, `Flag` model,
`PracticeLogBroker`) → Ingestion / Retrieval / Generation in parallel →
Voice Conversation (manual, wall-clock parallel) → Review (depends on
Retrieval + Generation Controllers and `Flag` model) → `app.py`
integration (factory, controller wiring, `/api/events` SSE, Origin/Referer
check, serve `frontend/dist` — owned by main session, no single
feature/agent owns it) → frontend per feature.

### Hierarchical Agent Delegation

General convention for any multi-step work that splits into judgment work plus
bounded mechanical work at meaningful scale (roughly 3+ independent, parallelizable
sub-tasks) — not limited to Standard layer builds. Established from the audit +
Phase 3 planning pipeline that produced
`decisions/phase-3-architectural-foundation-rebuild.md`. Full rationale and worked
example: `Projects/spanish-companion/decisions/hierarchical-agent-delegation.md`
(Obsidian).

| Tier | Model | Role | Use for |
|---|---|---|---|
| Plan/Orchestrate | Opus | Task decomposition, wave/dependency ordering, synthesizing parallel worker output, verification-bounce decisions | Any judgment call needing whole picture — no single worker sees full dependency graph |
| Audit/Build | Sonnet | Existing Broker/Foundation/Processing/Orchestration/Aggregation/Exposer Agents, and Auditor Agent | Unchanged from current practice — actual code generation and Standard-rule checking |
| Worker | Haiku | Bounded, mechanical, no-judgment sub-tasks against fully self-contained input | Parallel fan-out extraction/transformation — each sub-task independent, no synthesis required |

**Verification-bounce protocol** (mirrors existing Auditor Agent convention): a Plan/Orchestrate-tier pass checks Worker or Audit/Build output against source input before accepting it. On failure, bounce back to originating tier for correction — cap at 3 cycles, then escalate to user rather than looping indefinitely.

**Do not apply this for its own sake.** A single bug fix, small sequential task, or
work with no natural judgment/mechanical split doesn't need tiering — dispatch
directly.

**Model tiering is enforced, not advisory.** `~/.claude/plugins/marketplaces/pwongchaiya-toolkit/checks/check_agent_models.py`
fails if agent's `model:` frontmatter drifts from its tier, or if a new agent
isn't listed. Four of eleven agents had silently inverted tiers before this landed
(2026-09-10). When dispatching ad-hoc subagents, pass tier's model explicitly —
a fan-out that defaults to Opus is how this project exhausted a session limit.

**Register every background dispatch before launching it.** An agent killed by an
HTTP 429 cannot run cleanup, so record has to exist beforehand:

```bash
python ~/.claude/plugins/marketplaces/pwongchaiya-toolkit/scripts/stall_ledger.py register --vault "$VAULT" --project spanish-companion --id <id> --label "<what it is>"
python ~/.claude/plugins/marketplaces/pwongchaiya-toolkit/scripts/stall_ledger.py done     --vault "$VAULT" --project spanish-companion --id <id>
python ~/.claude/plugins/marketplaces/pwongchaiya-toolkit/scripts/stall_ledger.py stalled  --vault "$VAULT" --project spanish-companion --id <id> --reset "<reset text from the 429>"
```

`SessionStart` reports anything left standing. Resume a decision — confirm with
user before relaunching stalled work, even once limit has reset.

### Slash Commands

| Command | Purpose |
| --- | --- |
| `/session-start` | Planner read Obsidian state, brief on project status |
| `/session-end` | Sync Obsidian state.md, session log, MEMORY.md |
| `/compact` | Context window manage |

---

## Codebase Documentation (repowise)

Repo-level MCP indexer (`mcp__repowise__*` tools) — architecture overview,
context doc on file/symbol, change-risk assess, dead-code
detect, semantic search. Index per-repo, does **not** auto-update
on commit.

### When to use

- "How does X relate to Y" / architecture-overview question →
  `get_overview` / `get_context` before manual reading multiple files
- Symbol lookup or "why does this exist" → `get_symbol` / `get_why`
- Assess blast radius of change → `get_change_risk` / `get_risk`
- Free-text/semantic question across codebase → `search_codebase` /
  `get_answer`
- Find unused code → `get_dead_code`

### When not to

- Exact string/pattern search → `Grep`, not repowise (repowise
  semantic, not literal)
- File whose path already known → `Read` directly
- Anything touching code changed very recently — check SessionStart
  staleness warning first; if index behind HEAD, verify repowise's
  answer against live file before trusting it (see Phase 3's "verify
  against actual current code, not stale docs" rule above — same
  applies to stale index)

### Keeping it current

If SessionStart hook reports index behind HEAD, tell user to
run `repowise update` — never run it yourself.

---

## Obsidian Vault

Vault path: `c:\Users\pwong\OneDrive\Documents\Obsidian\Notes`

### When to read

- At `/session-start`: read `Projects/spanish-companion/state.md` for current
  build stage and pending work.
- When concept comes up, check `Projects/concepts/` before answering from
  training data.

### When to write

- At `/session-end`: save session summary to
  `Projects/spanish-companion/sessions/YYYY-MM-DD-HHmm.md`.
- When new architectural decision made (e.g. deviating from scope
  doc's build order): create note in `Projects/spanish-companion/decisions/`.

### Key vault files

| File | Purpose |
| --- | --- |
| `Projects/spanish-companion/state.md` | Build stage tracker, pending work |
| `Projects/spanish-companion/sessions/` | Per-session summaries |
| `Projects/spanish-companion/decisions/` | Architectural decision records |

---

## Files to Ignore

- `.env` and any `*.env` file
- `data/corpus/` (raw fetched RAE pages)
- `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`
- `.claude/` (machine-specific settings, not committed — agents/commands come
  from the `standard` plugin, no local copies)