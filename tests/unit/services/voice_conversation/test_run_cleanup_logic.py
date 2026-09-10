"""Unit test for ConversationOrchestrationService.run()'s finally-block cleanup.

W3 of the architecture conformance audit: the turn-state write used to run
first and unguarded in that block, so an OSError from it aborted the rest
and lost both the session log and the flags. This is the check that fails
if that ordering/guarding regresses.

Per CLAUDE.md's Phase 2 test strategy: every broker/service dependency is
Mock(spec=...), no live I/O, no pipecat pipeline -- _setup is stubbed out
so only run()'s cleanup path is exercised.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.local.audio import LocalAudioTransport

from api.brokers.configuration import ConfigurationBroker
from api.brokers.logging import LoggingBroker
from api.brokers.session_log import SessionLogBroker
from api.brokers.stt import SttBroker
from api.models.foundations.session_log.exceptions import SessionLogDependencyException
from api.services.foundations.flag import IFlagService
from api.services.foundations.live_transcript import ILiveTranscriptService
from api.services.foundations.session_log import ISessionLogService
from api.services.orchestrations.voice_conversation import ConversationOrchestrationService


@pytest.fixture
def mocks():
    return {
        "stt_broker": Mock(spec=SttBroker),
        "transport": Mock(spec=LocalAudioTransport),
        "tts": Mock(spec=AzureTTSService),
        "llm": Mock(spec=GoogleLLMService),
        "session_log_service": Mock(spec=ISessionLogService),
        "live_transcript_service": Mock(spec=ILiveTranscriptService),
        "flag_service": Mock(spec=IFlagService),
        "session_log_broker": Mock(spec=SessionLogBroker),
        "logging_broker": Mock(spec=LoggingBroker),
        "configuration_broker": Mock(spec=ConfigurationBroker),
    }


@pytest.fixture
def orchestrator(mocks):
    instance = ConversationOrchestrationService(**mocks)
    context = Mock()
    context.messages = []
    runner = Mock()
    runner.run = AsyncMock()

    async def _setup():
        return runner, context, []

    instance._setup = _setup
    # run() spawns _write_live_transcript as a background task; stub it so the
    # test never touches the real 1-second poll loop.
    instance._write_live_transcript = AsyncMock()
    instance._watch_for_stop_signal = AsyncMock()
    return instance


class TestRunCleanup:
    def test_saves_session_log_and_flags_when_turn_state_write_fails(self, orchestrator, mocks):
        mocks["session_log_broker"].write_turn_state.side_effect = OSError("disk full")
        mocks["session_log_service"].save.return_value = None

        asyncio.run(orchestrator.run())

        assert mocks["session_log_service"].save.call_count == 1
        assert mocks["flag_service"].save_flags.call_count == 1
        assert mocks["logging_broker"].log_error.call_count == 1

    def test_writes_idle_turn_state_after_saving(self, orchestrator, mocks):
        calls = []
        mocks["session_log_service"].save.side_effect = lambda *a: calls.append("save") or None
        mocks["session_log_broker"].write_turn_state.side_effect = lambda s: calls.append(f"turn_state:{s}")

        asyncio.run(orchestrator.run())

        assert calls == ["save", "turn_state:idle"]

    def test_saves_flags_and_turn_state_when_session_log_save_fails(self, orchestrator, mocks):
        mocks["session_log_service"].save.side_effect = SessionLogDependencyException(OSError("disk full"))

        asyncio.run(orchestrator.run())

        assert mocks["flag_service"].save_flags.call_count == 1
        assert mocks["session_log_broker"].write_turn_state.call_count == 1
        assert mocks["logging_broker"].log_error.call_count == 1
