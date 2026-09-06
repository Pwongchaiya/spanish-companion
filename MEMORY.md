# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-05-2158.md — toolkit
session-lifecycle tooling only, no application code. Measured the current
lifecycle from 76 real invocations (`/session-end` costs 3.04M tokens
median, 99.5% cache-read) and named 7 defects (L1-L7). Fixed and committed:
**L4** (ledger staleness — only the newest checkpoint segment ever survived
a `/clear`; now the whole unflushed chain does), **L5** (session
open/closed state, advisory not a lock — a `/clear` false-positive shipped
and was caught and fixed same session), **L6** (`state.md`'s
checkpoint-sync sentinel integrity now enforced, was ordering-by-prose
only), and **L1** (`/session-end` Step 1 no longer reconstructs facts from
context — `session_facts.py` gets date/branch/commits/files in one call).
A rebuild-the-lifecycle recommendation was made, then flipped by a
devil's-advocate pass, then both sides of that debate were found wrong when
the falsification test exposed a 2.1x turn-counting bug in the measuring
instrument itself. `next-session-prompt.md` deleted (137 lines, zero
invocations ever). 79 tests, seven suites, all passing at session end.
Decision records: `wiki/decisions/session-lifecycle-cost-and-stability-audit.md`,
`wiki/decisions/session-lifecycle-redesign-brainstorm.md`. **Open:** L2
(step batching) untouched; the auto-close hook is disabled pending one real
session without misfiring; L1's actual saving is unmeasured until the next
`/session-end` — check with `lifecycle_cost.py --since 2026-09-06`. Also
hit the documented stale-command-cache bug a 4th time, on this exact
`/session-end` invocation — worked around by reading the file directly.


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
