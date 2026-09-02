"""Unit tests for ReviewOrchestrator.list_flags() -- pass-through.

No exceptions file: FlagService.list_flags() returns [] for a missing or
corrupt file by contract, and "no flags yet" is a normal state, so
list_flags() has no failure mode of its own to test.
"""


class TestReviewOrchestratorListFlags:

    def test_should_return_service_flags_when_flags_exist(self, service, mock_flag_service, make_flag):
        # given
        flags = [make_flag("flag-1"), make_flag("flag-2")]
        mock_flag_service.list_flags.return_value = flags

        # when
        actual = service.list_flags()

        # then
        assert actual == flags
        mock_flag_service.list_flags.assert_called_once_with()

    def test_should_return_empty_list_when_service_has_no_flags(self, service, mock_flag_service):
        # given
        mock_flag_service.list_flags.return_value = []

        # when
        actual = service.list_flags()

        # then
        assert actual == []
        mock_flag_service.list_flags.assert_called_once_with()
