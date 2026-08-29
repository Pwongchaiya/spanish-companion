"""Unit tests for ConversationSessionService.get_status() -- the
ready-vs-running distinction. This is the actual bug-fix motivation for this
service (Phase 1 conflated "process started" with "pipeline warm"); see the
module docstring in api/services/session_lifecycle.py.
"""

from api.services.session_lifecycle import READY_WARMUP_SECONDS


class TestConversationSessionServiceGetStatus:

    def test_should_report_not_running_and_not_ready_when_never_started(self, service, mock_broker):
        # given
        mock_broker.is_running.return_value = False

        # when
        status = service.get_status()

        # then
        assert status.running is False
        assert status.ready is False
        assert status.graceful is None
        mock_broker.is_running.assert_called_once_with()

    def test_should_report_running_and_not_ready_immediately_after_start(
        self, service, mock_broker
    ):
        # given
        mock_broker.is_running.return_value = False
        service.start()
        mock_broker.reset_mock()  # isolate get_status()'s own broker calls
        mock_broker.is_running.return_value = True

        # when
        status = service.get_status()

        # then
        assert status.running is True
        assert status.ready is False
        mock_broker.is_running.assert_called_once_with()

    def test_should_report_ready_once_warmup_duration_has_elapsed(self, service, mock_broker, clock):
        # given
        mock_broker.is_running.return_value = False
        service.start()
        mock_broker.reset_mock()
        mock_broker.is_running.return_value = True
        clock.advance(READY_WARMUP_SECONDS)

        # when
        status = service.get_status()

        # then
        assert status.ready is True
        mock_broker.is_running.assert_called_once_with()

    def test_should_report_not_ready_just_before_warmup_duration_elapses(
        self, service, mock_broker, clock
    ):
        # given
        mock_broker.is_running.return_value = False
        service.start()
        mock_broker.reset_mock()
        mock_broker.is_running.return_value = True
        clock.advance(READY_WARMUP_SECONDS - 1)

        # when
        status = service.get_status()

        # then
        assert status.ready is False
        mock_broker.is_running.assert_called_once_with()

    def test_should_report_not_ready_when_process_exited_after_being_warm(
        self, service, mock_broker, clock
    ):
        # given -- process was warm, then died; running flips ready off too
        mock_broker.is_running.return_value = False
        service.start()
        mock_broker.reset_mock()
        clock.advance(READY_WARMUP_SECONDS)
        mock_broker.is_running.return_value = False

        # when
        status = service.get_status()

        # then
        assert status.running is False
        assert status.ready is False
        mock_broker.is_running.assert_called_once_with()
