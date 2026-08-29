# Generation service -- no integration tier (intentional, per CLAUDE.md)

## Decision

GenerationService has exactly one dependency, GenerationBroker, which wraps
the Gemini API -- an external API that CLAUDE.md's own Integration-tier rule
says gets "mocked at the Broker boundary" even at this tier.

Per CLAUDE.md's Phase 2 test strategy (Section "Testing Standards"):

> **Integration** (`tests/integration/services/<feature>/`): real test Postgres,
> external APIs (Azure Speech, Gemini) mocked at the Broker boundary.

There is no real infrastructure behind this feature (no Postgres, no filesystem,
no other in-process collaborator) for an integration test to exercise that the
Unit tier (`tests/unit/services/generation/`) doesn't already cover with the
same `Mock(spec=GenerationBroker)`. The integration tier exists to verify that:

1. A service correctly reads/writes the real infrastructure it depends on
   (Postgres, filesystems, etc.)
2. Exception-mapping from broker failures works in a realistic context
3. Data round-trips through real infrastructure intact

For GenerationService, all three are covered by Unit tests:
- Exception-mapping (GenerationError -> fallback string) is pure logic
  with no infrastructure involvement
- The broker is already mocked at the boundary
- No real infrastructure to verify round-tripping against

Writing integration tests here would duplicate Unit tests exactly, violating
YAGNI (You Aren't Gonna Need It). This decision is documented here rather
than padded with redundant test files.

## If real integration seams appear later

If a real integration seam shows up -- e.g. a caching layer, retry logic,
or a fake HTTP layer in front of `GeminiGenerationBroker` to verify the
broker's own request/response handling -- that test belongs to either:

- The Broker (if testing broker-level concerns), or
- A new Service method (if testing service-level orchestration),
  both of which would merit their own integration tests at that point.
