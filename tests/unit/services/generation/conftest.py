"""Shared fixtures for GenerationService unit tests.

Per CLAUDE.md's Phase 2 test strategy: GenerationBroker is mocked via
unittest.mock.Mock(spec=GenerationBroker) -- no real Gemini/network calls.

#64: ConfigurationBroker is faked (FakeConfigurationBroker, same
dict-backed shape as tests/unit/services/review/conftest.py's) rather than
reading real env vars, so EXPLAIN_TOP_K is a fixed, known test value -- the
`explain()` param renamed from a single `chunk` to `chunks` (a list); the
`chunk`/`other_chunk`/`chunks` fixtures below let existing single-chunk
tests keep asserting against one chunk's content while new top-k tests use
the list.
"""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from rag.brokers.generation import GenerationBroker
from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.generation import GenerationService
from tests.unit.services._rag_logging_fixture import mock_logging_broker  # noqa: F401

EXPLAIN_TOP_K = 3


@dataclass
class SimpleFlag:
    """Minimal stand-in satisfying services.generation.FlagLike structurally."""

    said: str
    corrected: str
    category: str


class FakeConfigurationBroker:
    """Dict-backed ConfigurationBroker stub -- fixed, known config values."""

    def __init__(self, values: dict) -> None:
        self._values = values

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._values.get(key, default)

    def require(self, key: str) -> str:
        return self._values[key]


@pytest.fixture
def mock_broker():
    return Mock(spec=GenerationBroker)


@pytest.fixture
def configuration_broker():
    return FakeConfigurationBroker({"EXPLAIN_TOP_K": str(EXPLAIN_TOP_K)})


@pytest.fixture
def service(mock_broker, mock_logging_broker, configuration_broker):
    return GenerationService(
        broker=mock_broker, logging_broker=mock_logging_broker, configuration_broker=configuration_broker
    )


@pytest.fixture
def flag():
    return SimpleFlag(said="yo soy tener", corrected="yo tengo", category="verb_conjugation")


@pytest.fixture
def chunk():
    return ScoredChunk(
        chunk_id=1,
        topic="preterite_vs_imperfect",
        source_url="https://rae.es/some-topic",
        content="El verbo 'tener' se conjuga como 'tengo' en primera persona del presente.",
        score=0.87,
    )


@pytest.fixture
def other_chunk():
    return ScoredChunk(
        chunk_id=2,
        topic="preterite_vs_imperfect",
        source_url="https://rae.es/other-topic",
        content="El pretérito se usa para acciones puntuales y terminadas en el pasado.",
        score=0.5,
    )


@pytest.fixture
def chunks(chunk, other_chunk):
    """Best-first list -- `chunk` (fixture above) stays the top-ranked one,
    so every existing single-chunk assertion (source_url/source_excerpt ==
    `chunk`'s) still holds unchanged.
    """
    return [chunk, other_chunk]
