# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-08-28-2026.md — Adopted repowise
(codebase-intelligence MCP tool) proactively, before the repo grows large.
Installed isolated via pipx after a direct pip install into the project venv
downgraded google-genai/rich and risked breaking the working voice pipeline;
restored those versions, reinstalled via pipx instead. Ran keyless init (no
LLM key, no CLAUDE.md touch) — 18 files indexed, 16 wiki pages, MCP wired
into Claude Code/VS Code. Kept repowise's hooks global (user's explicit
choice) despite rag-bench's own prior repowise decision going the opposite
way after a global-registration leak. Step 6 latency-fix reassessment from
the prior session is still open and untouched, awaiting user go-ahead.

---

## Vault Structure Reference

| Location | Path | What lives there |
| --- | --- | --- |
| Project state | Projects/spanish-companion/state.md | MVP stage tracker, pending work, last session pointer |
| Session summaries | Projects/spanish-companion/sessions/ | One file per session — YYYY-MM-DD-HHmm.md |
| Architectural decisions | Projects/spanish-companion/decisions/ | One file per decision — kebab-case slug |
