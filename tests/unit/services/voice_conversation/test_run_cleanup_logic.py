"""Unit test for ConversationOrchestrationService.run()'s finally-block cleanup.

W3 of the architecture conformance audit: the turn-state write used to run
first and unguarded in that block, so an OSError from it aborted the rest
and lost both the session log and the flags. This is the check that fails
if that ordering/guarding regresses.

Also covers the roadmap C1/C3 `session_log` row this method opens before
the pipeline runs and completes in the same finally block -- including that
neither write can take down a live conversation, which is the only reason
they live here rather than behind /start and /stop.

Per CLAUDE.md's Phase 2 test strategy: every broker/service dependency is
Mock(spec=...), no live I/O, no pipecat pipeline -- _setup is stubbed out
so only run()'s cleanup path is exercised.
"""

import asyncio
from datetime import datetime
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
from api.models.foundations.session_log_entry.exceptions import SessionLogEntryDependencyException
from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.services.foundations.flag import IFlagService
from api.services.foundations.learner_profile import ILearnerProfileService
from api.services.foundations.live_transcript import ILiveTranscriptService
from api.services.foundations.session_log import ISessionLogService
from api.services.foundations.session_log_entry import ISessionLogEntryService
from api.services.orchestrations.voice_conversation import ConversationOrchestrationService
from api.services.processings.learner_profile import ILearnerProfileProcessingService
from rag.services.foundations.generation import IGenerationService


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
        "session_log_entry_service": Mock(spec=ISessionLogEntryService),
        "generation_service": Mock(spec=IGenerationService),
        "learner_profile_processing_service": Mock(spec=ILearnerProfileProcessingService),
        "learner_profile_service": Mock(spec=ILearnerProfileService),
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


class TestSessionLogEntry:
    """Roadmap C1/C3: the session_log row opened before the pipeline runs
    and completed in run()'s finally block."""

    def test_records_scenario_slug_from_config_on_the_opened_row(self, orchestrator, mocks):
        # D4: the bot subprocess learns its scenario via SESSION_SCENARIO_SLUG.
        mocks["configuration_broker"].get.return_value = "ordering_coffee"
        mocks["session_log_entry_service"].create_session_log_entry.return_value = None
        runner = Mock()
        runner.run = AsyncMock()
        context = Mock()
        context.messages = []

        async def _setup():
            return runner, context, []

        orchestrator._setup = _setup

        asyncio.run(orchestrator.run())

        assert mocks["configuration_broker"].get.call_args_list[0].args == ("SESSION_SCENARIO_SLUG",)
        assert mocks["session_log_entry_service"].create_session_log_entry.call_count == 1
        assert mocks["session_log_entry_service"].create_session_log_entry.call_args.args[1] == "ordering_coffee"

    def test_opens_row_before_pipeline_and_completes_it_with_flag_count(self, orchestrator, mocks):
        entry = SessionLogEntry(id=42, started_at=datetime(2026, 1, 2, 10, 0), ended_at=None, flag_count=0)
        mocks["session_log_entry_service"].create_session_log_entry.return_value = entry
        # Two flags captured during the session -- _setup's stub returns the
        # list run() hands to cleanup, so seed it there.
        flags = [Mock(), Mock()]
        runner = Mock()
        runner.run = AsyncMock()
        context = Mock()
        context.messages = []

        async def _setup():
            return runner, context, flags

        orchestrator._setup = _setup

        asyncio.run(orchestrator.run())

        assert mocks["session_log_entry_service"].create_session_log_entry.call_count == 1
        assert mocks["session_log_entry_service"].complete_session_log_entry.call_count == 1
        entry_id, _ended_at, flag_count = mocks[
            "session_log_entry_service"
        ].complete_session_log_entry.call_args.args
        assert entry_id == 42
        assert flag_count == 2, "flag_count must be the in-memory session_flags length, not a re-read of flags.json"

    def test_records_zero_flag_count_for_a_clean_session(self, orchestrator, mocks):
        # C3's entire premise: a zero-flag session must be written as 0, not
        # skipped as falsy.
        mocks["session_log_entry_service"].create_session_log_entry.return_value = SessionLogEntry(
            id=1, started_at=datetime(2026, 1, 2, 10, 0), ended_at=None, flag_count=0
        )

        asyncio.run(orchestrator.run())

        assert mocks["session_log_entry_service"].complete_session_log_entry.call_args.args[2] == 0

    def test_conversation_survives_a_failed_row_open(self, orchestrator, mocks):
        mocks["session_log_entry_service"].create_session_log_entry.side_effect = (
            SessionLogEntryDependencyException(OSError("db down"))
        )

        asyncio.run(orchestrator.run())

        # No id to complete against, so completion is skipped entirely --
        # but the session's own data still got saved.
        assert mocks["session_log_entry_service"].complete_session_log_entry.call_count == 0
        assert mocks["session_log_service"].save.call_count == 1
        assert mocks["flag_service"].save_flags.call_count == 1
        assert mocks["logging_broker"].log_error.call_count == 1

    def test_cleanup_survives_a_failed_row_completion(self, orchestrator, mocks):
        mocks["session_log_entry_service"].create_session_log_entry.return_value = SessionLogEntry(
            id=1, started_at=datetime(2026, 1, 2, 10, 0), ended_at=None, flag_count=0
        )
        mocks["session_log_entry_service"].complete_session_log_entry.side_effect = (
            SessionLogEntryDependencyException(OSError("db down"))
        )

        asyncio.run(orchestrator.run())

        assert mocks["session_log_service"].save.call_count == 1
        assert mocks["flag_service"].save_flags.call_count == 1
        assert mocks["session_log_broker"].write_turn_state.call_count == 1
        assert mocks["logging_broker"].log_error.call_count == 1
