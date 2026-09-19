"""Unit tests for ConversationOrchestrationService._estimate_and_persist_cefr_level().

Roadmap A6. The rest of voice_conversation_service.py has no unit test tier
per CLAUDE.md's Layer-Agent Mapping ("Voice Conversation: no agent, any
layer... Gate on manual hardware/mic test") -- but this one private method
touches no pipecat/hardware at all, it's plain mock-testable orchestration
logic (same shape as ReviewOrchestrationService.record_practice's own
ensure_profile()-then-update composition), so it gets the same "leave one
runnable check" coverage every other branch of business logic in this
project does.
"""

from unittest.mock import Mock

import pytest

from api.services.orchestrations.voice_conversation.voice_conversation_service import (
    ConversationOrchestrationService,
)


@pytest.fixture
def service():
    return ConversationOrchestrationService(
        stt_broker=Mock(),
        transport=Mock(),
        tts=Mock(),
        llm=Mock(),
        session_log_service=Mock(),
        live_transcript_service=Mock(),
        flag_service=Mock(),
        session_log_broker=Mock(),
        session_log_entry_service=Mock(),
        generation_service=Mock(),
        learner_profile_processing_service=Mock(),
        learner_profile_service=Mock(),
        logging_broker=Mock(),
        configuration_broker=Mock(get=Mock(return_value="beginner")),
    )


class TestEstimateAndPersistCefrLevel:

    def test_should_skip_when_transcript_is_empty(self, service):
        service._live_transcript_service.read_full_text.return_value = ""

        service._estimate_and_persist_cefr_level()

        service._generation_service.estimate_cefr_level.assert_not_called()
        service._learner_profile_processing_service.ensure_profile.assert_not_called()

    def test_should_skip_persisting_when_estimate_is_none(self, service):
        service._live_transcript_service.read_full_text.return_value = "[user] hola"
        service._generation_service.estimate_cefr_level.return_value = None

        service._estimate_and_persist_cefr_level()

        service._learner_profile_processing_service.ensure_profile.assert_not_called()
        service._learner_profile_service.update_learner_profile.assert_not_called()

    def test_should_persist_estimate_via_ensure_profile_then_update(self, service):
        service._live_transcript_service.read_full_text.return_value = "[user] hola, como estas"
        service._generation_service.estimate_cefr_level.return_value = "B1"
        profile = Mock(id=42)
        service._learner_profile_processing_service.ensure_profile.return_value = profile

        service._estimate_and_persist_cefr_level()

        service._learner_profile_processing_service.ensure_profile.assert_called_once_with("beginner")
        service._learner_profile_service.update_learner_profile.assert_called_once_with(42, cefr_estimate="B1")

    def test_should_swallow_any_failure_without_raising(self, service):
        service._live_transcript_service.read_full_text.side_effect = RuntimeError("db down")

        service._estimate_and_persist_cefr_level()  # must not raise

        assert service._logging_broker.log_error.call_count == 1
