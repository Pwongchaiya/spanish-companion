# MEMORY.md — Obsidian Vault Index

Local index of spanish-companion project files in the Obsidian vault.
Read this before searching the vault. All paths are relative to vault root.
Updated automatically by /session-end (Last Session).

---

## Last Session

Projects/spanish-companion/sessions/2026-09-05-2305.md — continued the
22:35 toolkit session-lifecycle work, no application code. Closed L3
(`/checkpoint` no longer inlines a 37-line transcript parser —
`session_facts.py` gained `session_tokens()`) and most of L7: found
`sync_commands.py` was copy-only and had left `next-session-prompt.md`
(137 lines, zero recorded invocations) loading for a full session after
its deletion from the toolkit — fixed to prune orphans, guarded so an
absent toolkit source deletes nothing; and replaced `/session-start`'s
Steps 2b/2c (96 lines of failsafe-slug/staleness prose) with
`session_precheck.py`. Loaded lifecycle spec: 907 → 687 lines. 3 toolkit
commits (`a518b8f` L3, `426fdd0` sync pruning, `1bea38f` L7 session-start),
each its own submodule bump. **Open:** L1 still n=1 (this /session-end
makes n=2, still no signal); L2 and `session-end.md`'s 334 lines remain
deliberately held until L1 has data. Decision record updated:
`wiki/decisions/session-lifecycle-cost-and-stability-audit.md`.


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
