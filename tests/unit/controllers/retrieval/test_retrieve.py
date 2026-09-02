"""Unit tests for RetrievalController.retrieve() -- pure pass-through.

Per CLAUDE.md's Phase 2 Layer-Agent Mapping: this in-process controller has
no HTTP response to map, so it gets Unit tier only (no Acceptance tests).
"""

from unittest.mock import Mock

import pytest

from rag.controllers.retrieval import RetrievalController
from rag.models.retrieval import ScoredChunk
from rag.services.orchestrations.retrieval import HybridRetrievalService


@pytest.fixture
def mock_service():
    return Mock(spec=HybridRetrievalService)


@pytest.fixture
def controller(mock_service):
    return RetrievalController(mock_service)


@pytest.fixture
def chunks():
    return [
        ScoredChunk(
            chunk_id=1,
            topic="preterite_vs_imperfect",
            source_url="https://rae.es/some-topic",
            content="some grammar content",
            score=0.9,
        )
    ]


class TestRetrievalControllerRetrieve:

    def test_should_return_service_result_unchanged(self, controller, mock_service, chunks):
        # given
        mock_service.retrieve.return_value = chunks

        # when
        result = controller.retrieve(query="por vs para", top_k=3, category="prepositions")

        # then
        assert result is chunks

    def test_should_call_service_with_exact_arguments(self, controller, mock_service, chunks):
        # given
        mock_service.retrieve.return_value = chunks

        # when
        controller.retrieve(query="por vs para", top_k=3, category="prepositions")

        # then
        mock_service.retrieve.assert_called_once_with("por vs para", 3, "prepositions")

    def test_should_forward_none_category_when_not_provided(self, controller, mock_service, chunks):
        # given
        mock_service.retrieve.return_value = chunks

        # when
        controller.retrieve(query="por vs para", top_k=3)

        # then
        mock_service.retrieve.assert_called_once_with("por vs para", 3, None)
