"""Shared fixtures for Acceptance-tier tests needing a real test Postgres.

Per CLAUDE.md's Phase 2 test strategy, acceptance tests use a real test
Postgres (`TEST_DATABASE_URL`, never `DATABASE_URL`). Mirrors
`tests/integration/conftest.py`'s TEST_DATABASE_URL loading/skip pattern;
kept as its own file rather than folded into that one so the
broker-focused integration conftest doesn't grow acceptance-only fixtures.

Schema is expected to already be migrated (`alembic upgrade head` with
TEST_DATABASE_URL as DATABASE_URL) -- these fixtures only truncate the
tables a test touches, they don't create them.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
def test_database_url() -> str:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set -- see .env.example")
    return TEST_DATABASE_URL


@pytest.fixture
def truncate_tables(test_database_url):
    """Factory fixture: call with the table name(s) a test wrote to, and
    they're truncated after the test regardless of pass/fail."""
    tables_to_clean: list[str] = []

    def _register(*table_names: str) -> None:
        tables_to_clean.extend(table_names)

    yield _register

    if not tables_to_clean:
        return
    engine = create_engine(test_database_url)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {', '.join(tables_to_clean)} RESTART IDENTITY CASCADE"))
    engine.dispose()
