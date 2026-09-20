"""Unit tests for GenerationService.generate_text() -- caller-built prompt passthrough."""

from rag.brokers.generation import GenerationError


class TestGenerationServiceGenerateText:

    def test_should_return_stripped_broker_answer(self, service, mock_broker):
        mock_broker.generate.return_value = "  memory text \n"

        assert service.generate_text("prompt") == "memory text"
        mock_broker.generate.assert_called_once_with("prompt")

    def test_should_return_none_on_empty_answer(self, service, mock_broker):
        mock_broker.generate.return_value = "   "

        assert service.generate_text("prompt") is None

    def test_should_return_none_when_broker_fails(self, service, mock_broker):
        mock_broker.generate.side_effect = GenerationError("boom")

        assert service.generate_text("prompt") is None
        mock_broker.generate.assert_called_once_with("prompt")
