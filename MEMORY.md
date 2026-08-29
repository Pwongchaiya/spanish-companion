# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-28-2222.md — Ran a four-agent
review of the shipped Phase 1 MVP (code audit, design critique, security
probe, live Playwright UI critique), surfacing ~14 findings including a
critical live-tested bug (page reload during an active session desyncs the
UI and traps the user). Rather than patch Phase 1, the user chose to hold
all fixes and design a Phase 2 rebuild instead: Broker → Service →
Controller with constructor DI, six features, a hybrid-retrieval Strategy
pattern, and a React + TypeScript + Vite frontend (not Next.js — that would
reopen the exact dual-process fragility already flagged). Architecture
pinned and written to `decisions/companion-architecture-broker-service-controller.md`,
visualized in an Obsidian canvas and a published artifact, and reflected in
CLAUDE.md's Architecture/Tech Stack/Agent Coordination sections. Several
items remain open before Phase 2 build starts (see state.md Pending Work) —
most notably the migration plan (incremental refactor vs. rewrite), not yet
decided.

---

## Vault Structure Reference

| Location | Path | What lives there |
| --- | --- | --- |
| Project state | Projects/spanish-companion/state.md | MVP stage tracker, pending work, last session pointer |
| Session summaries | Projects/spanish-companion/sessions/ | One file per session — YYYY-MM-DD-HHmm.md |
| Architectural decisions | Projects/spanish-companion/decisions/ | One file per decision — kebab-case slug |
