# Alembic Migrations — Chunk Store Schema

## Applying Migrations

To apply all pending migrations to the database:

```bash
alembic upgrade head
```

This command runs in sequence and is safe to re-run — Alembic tracks the current revision and applies only the migrations not yet executed.

## Current Schema

The `chunks` table stores corpus text segments, embeddings, and metadata:

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key, auto-generated |
| `topic` | String | RAE grammar topic (e.g., "preterite-vs-imperfect") |
| `source_url` | String | URL the chunk was extracted from |
| `content` | String | The chunk text itself |
| `embedding` | Vector(384) | pgvector 384-dim dense vector (paraphrase-multilingual-MiniLM-L12-v2) |
| `embedding_model_version` | String | Model name that produced this embedding (for mismatch detection) |
| `chunking_strategy_version` | String | Chunking algorithm version (for targeted re-ingestion) |
| `created_at` | DateTime | Row insertion time (server-default) |

A HNSW index on `embedding` enables fast cosine-distance search.

## Known Limitation: Duplicate Rows on Re-Ingestion

**The Problem:** The ingestion pipeline (rag/controllers/ingestion.py) has no read-path to
check whether a chunk already exists before inserting. Re-running the ingestion CLI against
an already-populated corpus inserts duplicate rows — each chunk is added again, doubling
the corpus size.

**Current Workaround (Informal, Not a Real Solution):** Drop and recreate the table before
re-ingesting:

```bash
# 1. Rollback the migration to drop the table
alembic downgrade 0001

# 2. Re-apply the migration to create a fresh schema
alembic upgrade head

# 3. Re-ingest the corpus
python -m rag.controllers.ingestion
```

This is documented here because it's the current stopping point — not because it's a
long-term fix. The canonical solution (a broker `exists()` method + idempotent ingestion)
is deferred; at MVP scale (3–5 topics, ~30–50 chunks), manual re-ingestion is acceptable.

**When to Use This Workaround:**
- You've run the ingestion CLI multiple times and want a clean corpus
- You're testing ingestion changes and need to reset state
- You want to switch embedding models and re-ingest the whole corpus from scratch

**Why It's Not a Real Fix:**
- Loses the entire corpus, including any manually flagged corrections or Review Mode history
- Requires explicit user action (no automation, no detection)
- A true solution would be: add a `ChunkRepositoryBroker.exists()` method that checks
  if a chunk's content already exists before inserting, and only insert if missing

## Migration History

- `0001_create_chunks_table.py` — Initial schema with version tracking (Phase 2, replaces Phase 1's raw-DDL table)
- `0002_create_learner_profile_tables.py` — `learner_profile`, `mistake_pattern`, `topic_covered` (learner memory / dynamic bot behavior, Phase 1 of that roadmap — see `decisions/dynamic-bot-behavior-and-learner-memory.md`)
