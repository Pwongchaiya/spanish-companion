"""Unit tests for GenerationController.explain() -- pure pass-through.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping: this in-process controller has
no HTTP response to map, so it gets Unit tier only (no Acceptance tests).
"""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from rag.controllers.generation import GenerationController
from rag.models.generation import Explanation
from rag.models.retrieval import ScoredChunk
from rag.services.generation import GenerationService


@dataclass
class SimpleFlag:
    """Minimal stand-in satisfying services.generation.FlagLike structurally."""

    said: str
    corrected: str
    category: str


@pytest.fixture
def mock_service():
    return Mock(spec=GenerationService)


@pytest.fixture
def controller(mock_service):
    return GenerationController(mock_service)


@pytest.fixture
def flag():
    return SimpleFlag(said="yo soy tener", corrected="yo tengo", category="verb_conjugation")


@pytest.fixture
def chunk():
    return ScoredChunk(
        chunk_id=1,
        topic="preterite_vs_imperfect",
        source_url="https://rae.es/some-topic",
        content="some grammar content",
        score=0.87,
    )


class TestGenerationControllerExplain:

    def test_should_return_service_result_unchanged(self, controller, mock_service, flag, chunk):
        # given
        expected = Explanation(explanation="some explanation", source_url=chunk.source_url)
        mock_service.explain.return_value = expected

        # when
        result = controller.explain(flag, chunk)

        # then
        assert result is expected

    def test_should_call_service_with_exact_arguments(self, controller, mock_service, flag, chunk):
        # given
        mock_service.explain.return_value = Explanation(explanation="x", source_url="y")

        # when
        controller.explain(flag, chunk)

        # then
        mock_service.explain.assert_called_once_with(flag, chunk)
