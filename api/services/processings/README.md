# Processing Services

`learner_profile/` — `ensure_profile()`, get-or-create on the singleton
profile row. First Processing service built under CLAUDE.md's Processing-row
reversal (2026-09-10). See `Projects/spanish-companion/entities/learner-profile.md`.

`mistake_pattern/` — higher-order logic on top of the MistakePattern
Foundation service. See `Projects/spanish-companion/entities/mistake-pattern.md`.

`topic_covered/` — `record_topic()` upsert (insert vs. touch) on top of the
TopicCovered Foundation service. See
`Projects/spanish-companion/entities/topic-covered.md`.

When another Processing service is needed, see
`.claude-toolkit/.claude/agents/processing-agent.md` for the scaffolding
pattern and build order.
