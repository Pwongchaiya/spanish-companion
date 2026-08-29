# Generation service -- no integration tier

GenerationService has exactly one dependency, GenerationBroker, which wraps
the Gemini API -- an external API that CLAUDE.md's own Integration-tier rule
says gets "mocked at the Broker boundary" even at this tier. There is no
real infrastructure behind this feature (no Postgres, no filesystem, no
other in-process collaborator) for an integration test to exercise that the
Unit tier (`tests/unit/services/generation/`) doesn't already cover with the
same `Mock(spec=GenerationBroker)`. Writing integration tests here would
just be the Unit tests copy-pasted against the same mock, so this tier is
skipped rather than padded with duplicates.

If a real integration seam shows up later -- e.g. a fake HTTP layer in front
of `GeminiGenerationBroker` to verify the broker's own request/response
handling -- that test belongs to the Broker, not this Service, and CLAUDE.md
already excludes Brokers from the test plan for this project.
