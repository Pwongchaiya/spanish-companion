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
| Embeddings | sentence-transformers, BGE-small |
| Corpus source | RAE grammar pages (MVP: 3-5 starter topics) |
| UI | Flask — minimal server, plain HTML/vanilla JS, no build tooling |
| Config | python-dotenv — single `.env` at repo root |

---

## Architecture

**Not entity/layer-based.** This project does not follow The Standard's
Broker → Foundation → Processing → Orchestration → Aggregation → Exposer
build sequence — there's no CRUD entity registry here. The build instead
follows the staged MVP plan tracked in `Projects/spanish-companion/state.md`
(Pending Work), mirrored from `spanish-companion-mvp-scope.md` Section 7:

1. Voice loop (Pipecat + Azure STT/TTS + Gemini), no flagging, no RAG.
2. Live error-flagging as a byproduct of the same generation call.
3. RAE corpus ingestion + dense-only retrieval (pgvector).
4. Review Mode v0: flagged list → selection → RAG-grounded explanation →
   single practice attempt.
5. Minimal UI over the above.
6. Reassess the Out-of-Scope list only after 1-5 work end-to-end.

Never build a later stage before the earlier one works — verify each stage
manually (per the scope doc's Build Order) before moving on.

Two runtime modes:
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

No Standard entity/layer build sequence for this project (see Architecture).
The Planner Agent still owns session continuity via `/session-start` /
`/session-end`, reading and writing `Projects/spanish-companion/state.md`.

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
