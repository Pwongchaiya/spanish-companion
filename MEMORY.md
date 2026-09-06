# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-05-2235.md — continued the
21:58 toolkit session-lifecycle work, no application code. Measured L1 for
the first time: n=1, landed exactly on the pre-L1 median (19 turns) — no
signal yet, recheck with `lifecycle_cost.py --project spanish-companion
--commands session-end --detail` after 3-5 more runs. Enabled
`session_tracker.py` (L5) for real via `.claude/settings.local.json`'s
`PostToolUse`/`Bash` hook — this session's own flush is its first live
close test. Closed Piece C, but not by its filed remedy: the
`Architecture Reference` section it asked to add to
`Projects/_templates/state.md` no longer exists in `session-end.md` (the
418→316 rewrite deleted the step that read it); the real defect was
`/project-init` and `/init-rag` both hand-rolling their own `state.md`
missing its frontmatter — both now read the canonical template instead.
Also fixed a genuinely red test found along the way:
`test_split_result.py` had asserted byte-identity on
`references/shared/dotnet-to-python.md` since 2026-09-04, but that file
was correctly hand-edited the same day (async→sync SQLAlchemy) — changed
to a structural check. New checks added: `test_settings_template.py`,
`test_command_templates.py` (caught `/project-init`'s inlined-template
copy on its first run, not named in the original plan). 6 toolkit
commits, 4 submodule bumps. **Open:** L2 (step batching) deliberately
held until L1 has a real sample — doing it now would make the two deltas
unattributable. Decision record updated:
`wiki/decisions/session-end-state-md-guard.md`.


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
