"""Unit test for ConversationOrchestrationService._flush_new_turns.

Extracted from _write_live_transcript to cut a nested_complexity finding
(repowise get_health: 4-level nesting). This is the check that fails if the
extraction regresses the original behavior -- append each unwritten turn,
stop and report the count written so far on a broker failure, resume from
there next call.

Per CLAUDE.md's Phase 2 test strategy: every broker/service dependency is
Mock(spec=...), no live I/O.
"""

from unittest.mock import Mock

from api.brokers.configuration import ConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.brokers.session_log import SessionLogBroker
from api.brokers.stt import SttBroker
from api.models.foundations.live_transcript.exceptions import LiveTranscriptServiceException
from api.services.foundations.flag import IFlagService
from api.services.foundations.learner_profile import ILearnerProfileService
from api.services.foundations.live_transcript import ILiveTranscriptService
from api.services.foundations.session_log import ISessionLogService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.orchestrations.voice_conversation import ConversationOrchestrationService
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.local.audio import LocalAudioTransport
from rag.services.foundations.generation import IGenerationService


def _make_orchestrator(**overrides):
    mocks = {
        "stt_broker": Mock(spec=SttBroker),
        "transport": Mock(spec=LocalAudioTransport),
        "tts": Mock(spec=AzureTTSService),
        "llm": Mock(spec=GoogleLLMService),
        "session_log_service": Mock(spec=ISessionLogService),
        "live_transcript_service": Mock(spec=ILiveTranscriptService),
        "flag_service": Mock(spec=IFlagService),
        "session_log_broker": Mock(spec=SessionLogBroker),
        "session_log_entry_service": Mock(spec=ISessionLogEntryService),
        "generation_service": Mock(spec=IGenerationService),
        "learner_profile_processing_service": Mock(spec=ILearnerProfileProcessingService),
        "learner_profile_service": Mock(spec=ILearnerProfileService),
        "logging_broker": Mock(spec=LoggingBroker),
        "configuration_broker": Mock(spec=ConfigurationBroker),
    }
    mocks.update(overrides)
    return ConversationOrchestrationService(**mocks), mocks


def _context(*turns):
    context = Mock()
    context.messages = [{"role": role, "content": text} for role, text in turns]
    return context


class TestFlushNewTurns:
    def test_appends_only_unwritten_turns_and_advances_count(self):
        orchestrator, mocks = _make_orchestrator()
        context = _context(("user", "hola"), ("assistant", "hola!"), ("user", "adios"))

        new_count = orchestrator._flush_new_turns(context, written_turn_count=2)

        assert new_count == 3
        mocks["live_transcript_service"].append.assert_called_once_with("user", "adios")

    def test_stops_and_returns_partial_count_on_broker_failure(self):
        orchestrator, mocks = _make_orchestrator()
        mocks["live_transcript_service"].append.side_effect = [
            None,
            LiveTranscriptServiceException(OSError("disk full")),
        ]
        context = _context(("user", "uno"), ("assistant", "dos"), ("user", "tres"))

        new_count = orchestrator._flush_new_turns(context, written_turn_count=0)

        assert new_count == 1
        assert mocks["live_transcript_service"].append.call_count == 2
        mocks["logging_broker"].log_error.assert_called_once()

    def test_ignores_non_user_assistant_messages(self):
        orchestrator, mocks = _make_orchestrator()
        context = _context(("system", "you are a bot"), ("user", "hola"))

        new_count = orchestrator._flush_new_turns(context, written_turn_count=0)

        assert new_count == 1
        mocks["live_transcript_service"].append.assert_called_once_with("user", "hola")
