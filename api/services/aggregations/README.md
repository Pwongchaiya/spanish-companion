# Aggregation Services

`session_recap/` (roadmap item C2, post-session recap card) is the first
feature to use this layer -- it composes ReviewOrchestrationService.list_flags()
and ProgressOrchestrationService.get_latest_completed_session() for a single
new Exposer route (`GET /progress/recap`), which is exactly the "Exposer
needs >1 Orchestration service" trigger this layer exists for.

When another Aggregation service is needed, see
`.claude-toolkit/.claude/agents/aggregation-agent.md` for the scaffolding
pattern and build order, and `session_recap/` for this project's first
worked example.
