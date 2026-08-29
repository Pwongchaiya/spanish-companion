"""Shared fixtures for Integration-tier tests (real test Postgres).

Per CLAUDE.md's Phase 2 test strategy: Integration tests use a real test
Postgres (TEST_DATABASE_URL, never DATABASE_URL) with external APIs mocked
at the Broker boundary. The schema is expected to already be migrated
(`alembic upgrade head` with TEST_DATABASE_URL as DATABASE_URL) -- this
fixture only truncates between tests, it does not create tables.
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
