"""Shared fixtures for Integration-tier tests (real test Postgres).

Per CLAUDE.md's Phase 2 test strategy: Integration tests use a real test
Postgres (TEST_DATABASE_URL, never DATABASE_URL) with external APIs mocked
at the Broker boundary. The schema is expected to already be migrated
(`alembic upgrade head` with TEST_DATABASE_URL as DATABASE_URL) -- this
fixture only truncates between tests, it does not create tables.

## Broker-level test exclusions

Per CLAUDE.md's note "No tests during build", the integration test plan
excludes broker-level tests:

**ChunkRepositoryBroker & EmbeddingModelBroker**: Integration tests ARE
written (in tests/integration/brokers/). These brokers have real infrastructure
worth verifying: pgvector query correctness and embedding model dimensions.

**FlagBroker & PracticeLogBroker**: Integration tests NOT written. These are
JSON file I/O brokers with lower risk: no query logic to verify, just
file read/write round-tripping. File I/O is a platform primitive (not a
custom implementation), and the tolerance for corrupt/missing/partial files
is already hardcoded in load_flags() and read_attempts() (return [] on any
error). The only risk worth preventing is mid-write reads (atomic write
via os.replace in FlagBroker), which is already implemented. Unit tests
(not written yet, deferred to later phase) would verify these codepaths if
needed.

**SubprocessBotProcessBroker**: Integration test exists (test_bot_process.py).
This broker wraps an OS process and needs real subprocess testing to verify
signal handling and process lifecycle.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
def chunk_repository():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set -- see .env.example")

    broker = SqlAlchemyChunkRepositoryBroker(connection_string=TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE chunks RESTART IDENTITY"))
    yield broker
    engine.dispose()
