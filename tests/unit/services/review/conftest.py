"""Shared fixtures for ReviewOrchestrationService unit tests.

Per CLAUDE.md's Phase 2 test strategy: all four dependencies are mocked via
unittest.mock.Mock(spec=...) -- the two api Foundation services at their
Protocol boundary, the two rag services at their class boundary (never their
real collaborators, which would drag in Postgres, an embedding model and
Gemini). datetime.now() is never read live: the clock is injected as a fake,
test-controlled callable, same pattern as
tests/unit/services/session_lifecycle/conftest.py.

ConfigurationBroker is likewise faked (FakeConfigurationBroker) rather than
reading real env vars -- the H1 audit finding removed RETRIEVAL_TOP_K as a
module-level, import-time env read; tests get the same fixed, known value
from this fake instead.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from api.brokers.logging import LoggingBroker
from api.models.foundations.flag import Flag
from api.services.foundations.flag import IFlagService
from api.services.foundations.practice_log import IPracticeLogService
from api.services.orchestrations.review import ReviewOrchestrationService
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.generation import GenerationService
from rag.services.orchestrations.retrieval import HybridRetrievalOrchestrationService

FIXED_NOW = datetime(2026, 1, 2, 3, 4, 5)
RETRIEVAL_TOP_K = 3


class FakeConfigurationBroker:
    """Dict-backed ConfigurationBroker stub -- fixed, known config values."""

    def __init__(self, values: dict) -> None:
        self._values = values

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._values.get(key, default)

    def require(self, key: str) -> str:
        return self._values[key]


class FakeClock:
    """Deterministic, manually-advanced stand-in for datetime.now."""

    def __init__(self, start: datetime = FIXED_NOW) -> None:
        self._now = start

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


@pytest.fixture
def mock_flag_service():
    return Mock(spec=IFlagService)


@pytest.fixture
def mock_practice_log_service():
    return Mock(spec=IPracticeLogService)


@pytest.fixture
def mock_retrieval_service():
    return Mock(spec=HybridRetrievalOrchestrationService)


@pytest.fixture
def mock_generation_service():
    return Mock(spec=GenerationService)


@pytest.fixture
def mock_logging_broker():
    return Mock(spec=LoggingBroker)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def configuration_broker():
    return FakeConfigurationBroker({"RETRIEVAL_TOP_K": str(RETRIEVAL_TOP_K)})


@pytest.fixture
def service(
    mock_flag_service,
    mock_practice_log_service,
    mock_retrieval_service,
    mock_generation_service,
    clock,
    configuration_broker,
    mock_logging_broker,
):
    return ReviewOrchestrationService(
        flag_service=mock_flag_service,
        practice_log_service=mock_practice_log_service,
        retrieval_service=mock_retrieval_service,
        generation_service=mock_generation_service,
        clock=clock,
        configuration_broker=configuration_broker,
        logging_broker=mock_logging_broker,
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
