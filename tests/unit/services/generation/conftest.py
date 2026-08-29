"""Shared fixtures for GenerationService unit tests.

Per CLAUDE.md's Phase 2 test strategy: GenerationBroker is mocked via
unittest.mock.Mock(spec=GenerationBroker) -- no real Gemini/network calls.
"""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from rag.brokers.generation import GenerationBroker
from rag.models.retrieval import ScoredChunk
from rag.services.generation import GenerationService


@dataclass
class SimpleFlag:
    """Minimal stand-in satisfying services.generation.FlagLike structurally."""

    said: str
    corrected: str
    category: str


@pytest.fixture
def mock_broker():
    return Mock(spec=GenerationBroker)


@pytest.fixture
def service(mock_broker):
    return GenerationService(broker=mock_broker)


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
