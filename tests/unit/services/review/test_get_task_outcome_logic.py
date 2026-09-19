"""Unit tests for ReviewOrchestrationService.get_task_outcome() -- roadmap D4.

Judging is lazy and Review-Mode-only: the LLM judge runs only when the latest
completed session has a task scenario, no stored outcome, and a transcript.
"""

from datetime import datetime

import pytest

from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry
from api.models.orchestrations.review.exceptions import ReviewOrchestrationServiceException

START = datetime(2026, 1, 2, 10, 0, 0)
END = datetime(2026, 1, 2, 10, 30, 0)
COFFEE_CONDITION = "The user successfully orders both a drink and a food item from the barista."


def entry(entry_id=1, slug="ordering_coffee", outcome=None, ended=END):
    return SessionLogEntry(
        id=entry_id, started_at=START, ended_at=ended, flag_count=0, scenario_slug=slug, task_outcome=outcome
    )


class TestGetTaskOutcomeLogic:

    def test_should_judge_persist_and_return_outcome_for_unjudged_task_session(
        self, service, mock_session_log_entry_service, mock_live_transcript_service, mock_generation_service
    ):
        # given
        mock_session_log_entry_service.list_session_log_entries.return_value = [entry(entry_id=5)]
        mock_live_transcript_service.read_full_text.return_value = "[user] un cafe y un pan"
        mock_generation_service.judge_task_outcome.return_value = "success"

        # when
        actual = service.get_task_outcome()

        # then
        assert (actual.scenario_slug, actual.label, actual.outcome) == ("ordering_coffee", "Ordering coffee", "success")
        assert actual.success_condition == COFFEE_CONDITION
        mock_generation_service.judge_task_outcome.assert_called_once_with("[user] un cafe y un pan", COFFEE_CONDITION)
        mock_session_log_entry_service.set_task_outcome.assert_called_once_with(5, "success")
        mock_session_log_entry_service.list_session_log_entries.assert_called_once_with()

    def test_should_not_rejudge_when_outcome_already_stored(
        self, service, mock_session_log_entry_service, mock_live_transcript_service, mock_generation_service
    ):
        # given
        mock_session_log_entry_service.list_session_log_entries.return_value = [entry(outcome="fail")]

        # when
        actual = service.get_task_outcome()

        # then
        assert actual.outcome == "fail"
        assert mock_generation_service.judge_task_outcome.call_count == 0
        assert mock_live_transcript_service.read_full_text.call_count == 0
        assert mock_session_log_entry_service.set_task_outcome.call_count == 0

    @pytest.mark.parametrize("slug", [None, "casual_chat", "nonexistent"])
    def test_should_return_none_when_session_has_no_task_scenario(
        self, service, mock_session_log_entry_service, mock_generation_service, slug
    ):
        # given
        mock_session_log_entry_service.list_session_log_entries.return_value = [entry(slug=slug)]

        # when / then
        assert service.get_task_outcome() is None
        assert mock_generation_service.judge_task_outcome.call_count == 0

    def test_should_return_none_when_no_completed_session(
        self, service, mock_session_log_entry_service, mock_generation_service
    ):
        # given -- only an in-flight row
        mock_session_log_entry_service.list_session_log_entries.return_value = [entry(ended=None)]

        # when / then
        assert service.get_task_outcome() is None
        assert mock_generation_service.judge_task_outcome.call_count == 0

    def test_should_use_latest_completed_session(
        self, service, mock_session_log_entry_service, mock_generation_service
    ):
        # given -- newest row is in flight, so the earlier completed one is used
        mock_session_log_entry_service.list_session_log_entries.return_value = [
            entry(entry_id=1, slug="casual_chat", outcome=None),
            entry(entry_id=2, outcome="success"),
            entry(entry_id=3, ended=None),
        ]

        # when
        actual = service.get_task_outcome()

        # then
        assert actual.scenario_slug == "ordering_coffee" and actual.outcome == "success"

    def test_should_leave_outcome_none_when_transcript_is_empty(
        self, service, mock_session_log_entry_service, mock_live_transcript_service, mock_generation_service
    ):
        # given
        mock_session_log_entry_service.list_session_log_entries.return_value = [entry()]
        mock_live_transcript_service.read_full_text.return_value = ""

        # when
        actual = service.get_task_outcome()

        # then
        assert actual.outcome is None
        assert mock_generation_service.judge_task_outcome.call_count == 0
        assert mock_session_log_entry_service.set_task_outcome.call_count == 0

    def test_should_not_persist_when_judge_cannot_decide(
        self, service, mock_session_log_entry_service, mock_live_transcript_service, mock_generation_service
    ):
        # given
        mock_session_log_entry_service.list_session_log_entries.return_value = [entry()]
        mock_live_transcript_service.read_full_text.return_value = "[user] hola"
        mock_generation_service.judge_task_outcome.return_value = None

        # when
        actual = service.get_task_outcome()

        # then
        assert actual.outcome is None
        assert mock_generation_service.judge_task_outcome.call_count == 1
        assert mock_session_log_entry_service.set_task_outcome.call_count == 0

    def test_should_wrap_storage_failure_as_service_exception(
        self, service, mock_session_log_entry_service, mock_logging_broker
    ):
        # given
        mock_session_log_entry_service.list_session_log_entries.side_effect = RuntimeError("db down")

        # when / then
        with pytest.raises(ReviewOrchestrationServiceException):
            service.get_task_outcome()
        mock_logging_broker.log_error.assert_called_once()
