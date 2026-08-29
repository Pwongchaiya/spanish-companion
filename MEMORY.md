# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-28-1947.md — Steps 3-6 built via
the opus(orchestrator)/sonnet(auditor)/haiku(worker) delegation model:
RAE corpus ingestion (rag/), RAG-grounded Review Mode (review/), minimal
Flask UI (ui/). User confirmed the full app works end-to-end via real manual
mic testing. Found and fixed 4 real bugs beyond what code review alone
caught (English-only embedding model, stale flags file, no Windows
CTRL_BREAK_EVENT handler, Flask debug-mode orphaning the subprocess). Step 6
reassessment open: 3 latency issues found in real use, fixes proposed,
awaiting user go-ahead to build.

---

## Vault Structure Reference

| Location | Path | What lives there |
| --- | --- | --- |
| Project state | Projects/spanish-companion/state.md | MVP stage tracker, pending work, last session pointer |
| Session summaries | Projects/spanish-companion/sessions/ | One file per session — YYYY-MM-DD-HHmm.md |
| Architectural decisions | Projects/spanish-companion/decisions/ | One file per decision — kebab-case slug |
