"""Unit tests for ConversationOrchestrationService._update_persona_memory() (teardown-only)."""

from unittest.mock import Mock

from api.brokers.prompt import PromptBroker
from api.services.orchestrations.voice_conversation.voice_conversation_service import (
    ConversationOrchestrationService,
)
from api.services.processings.persona import IPersonaProcessingService

CONFIG = {"SESSION_PERSONA": "marta", "PERSONA_MEMORY_MAX_CHARS": "20"}


def _make(config=None):
    config = CONFIG if config is None else config
    prompt_broker = Mock(spec=PromptBroker)
    prompt_broker.get_persona_memory_prompt.return_value = "M={memory}|T={transcript}|N={max_chars}"
    persona_service = Mock(spec=IPersonaProcessingService)
    persona_service.ensure_persona.return_value = Mock(memory="old")
    return ConversationOrchestrationService(
        stt_broker=Mock(),
        transport=Mock(),
        tts=Mock(),
        llm=Mock(),
        session_log_service=Mock(),
        live_transcript_service=Mock(read_full_text=Mock(return_value="[user] hola")),
        flag_service=Mock(),
        session_log_broker=Mock(),
        session_log_entry_service=Mock(),
        generation_service=Mock(),
        learner_profile_processing_service=Mock(),
        learner_profile_service=Mock(),
        logging_broker=Mock(),
        configuration_broker=Mock(get=Mock(side_effect=lambda k, d=None: config.get(k, d))),
        persona_processing_service=persona_service,
        prompt_broker=prompt_broker,
    )


class TestUpdatePersonaMemory:

    def test_should_merge_old_memory_and_transcript_then_update(self):
        s = _make()
        s._generation_service.generate_text.return_value = "x" * 50

        s._update_persona_memory()

        s._generation_service.generate_text.assert_called_once_with("M=old|T=[user] hola|N=20")
        s._persona_processing_service.update_memory.assert_called_once_with("marta", "x" * 20)

    def test_should_skip_when_transcript_is_empty(self):
        s = _make()
        s._live_transcript_service.read_full_text.return_value = ""

        s._update_persona_memory()

        s._generation_service.generate_text.assert_not_called()
        s._persona_processing_service.update_memory.assert_not_called()

    def test_should_skip_when_no_persona(self):
        s = _make({})

        s._update_persona_memory()

        s._live_transcript_service.read_full_text.assert_not_called()
        s._generation_service.generate_text.assert_not_called()
        s._persona_processing_service.update_memory.assert_not_called()

    def test_should_not_update_when_llm_returns_none(self):
        s = _make()
        s._generation_service.generate_text.return_value = None

        s._update_persona_memory()

        s._persona_processing_service.update_memory.assert_not_called()

    def test_should_warn_and_not_raise_when_llm_fails(self):
        s = _make()
        s._generation_service.generate_text.side_effect = RuntimeError("llm down")

        s._update_persona_memory()  # must not raise

        s._persona_processing_service.update_memory.assert_not_called()
        assert s._logging_broker.log_warning.call_count == 1
