"""Unit tests for ReviewOrchestrationService.list_flags() -- the happy paths.

FlagService.list_flags() returns [] for a missing or corrupt file by
contract, so "no flags yet" comes back as [] rather than an exception. Its
other failure modes now arrive here wrapped -- see
test_list_flags_exceptions.py.
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
