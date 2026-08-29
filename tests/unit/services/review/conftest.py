"""Shared fixtures for ReviewOrchestrator unit tests.

Per CLAUDE.md's Phase 2 test strategy: all four dependencies are mocked via
unittest.mock.Mock(spec=...) -- the two brokers at the Protocol boundary, the
two rag controllers at their class boundary (never their real services, which
would drag in Postgres, an embedding model and Gemini). datetime.now() is never
read live: the clock is injected as a fake, test-controlled callable, same
pattern as tests/unit/services/session_lifecycle/conftest.py.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.brokers.flag import FlagBroker
from api.brokers.practice_log import PracticeLogBroker
from api.models.flag import Flag
from api.services.review import ReviewOrchestrator
from rag.controllers.generation import GenerationController
from rag.controllers.retrieval import RetrievalController
from rag.models.retrieval import ScoredChunk

FIXED_NOW = datetime(2026, 1, 2, 3, 4, 5)


class FakeClock:
    """Deterministic, manually-advanced stand-in for datetime.now."""

    def __init__(self, start: datetime = FIXED_NOW) -> None:
        self._now = start

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


@pytest.fixture
def mock_flag_broker():
    return Mock(spec=FlagBroker)


@pytest.fixture
def mock_practice_log_broker():
    return Mock(spec=PracticeLogBroker)


@pytest.fixture
def mock_retrieval_controller():
    return Mock(spec=RetrievalController)


@pytest.fixture
def mock_generation_controller():
    return Mock(spec=GenerationController)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(
    mock_flag_broker,
    mock_practice_log_broker,
    mock_retrieval_controller,
    mock_generation_controller,
    clock,
):
    return ReviewOrchestrator(
        flag_broker=mock_flag_broker,
        practice_log_broker=mock_practice_log_broker,
        retrieval_controller=mock_retrieval_controller,
        generation_controller=mock_generation_controller,
        clock=clock,
    )


# Factories are fixtures, not module-level functions, so test modules never have
# to `from conftest import ...` -- two sibling conftest.py files (this one and
# session_lifecycle's) both import as `conftest` under pytest's default prepend
# mode, and which one wins depends on sys.path order.
@pytest.fixture
def make_flag():
    def _make(flag_id: str = "flag-1", corrected: str = "fui al mercado", category: str = "preterite") -> Flag:
        return Flag(
            id=flag_id,
            said="iba al mercado ayer",
            corrected=corrected,
            category=category,
            timestamp=FIXED_NOW,
        )

    return _make


@pytest.fixture
def make_chunk():
    def _make(chunk_id: int = 1, score: float = 0.9) -> ScoredChunk:
        return ScoredChunk(
            chunk_id=chunk_id,
            topic="preterite vs imperfect",
            source_url=f"https://rae.example/{chunk_id}",
            content=f"chunk {chunk_id} content",
            score=score,
        )

    return _make
