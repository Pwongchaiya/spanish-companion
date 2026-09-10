"""Unit tests for FlagService.list_flags() -- the happy paths.

FlagBroker.load_flags() returns [] for a missing or corrupt file by contract,
so "no flags yet" comes back as [] rather than an exception. Every other
broker failure is a real error -- see test_list_flags_exceptions.py.
"""


class TestFlagServiceListFlags:

    def test_should_return_broker_flags_when_flags_exist(self, service, mock_flag_broker, make_flag):
        # given
        flags = [make_flag("flag-1"), make_flag("flag-2")]
        mock_flag_broker.load_flags.return_value = flags

        # when
        actual = service.list_flags()

        # then
        assert actual == flags
        mock_flag_broker.load_flags.assert_called_once_with()

    def test_should_return_empty_list_when_broker_has_no_flags(self, service, mock_flag_broker):
        # given
        mock_flag_broker.load_flags.return_value = []

        # when
        actual = service.list_flags()

        # then
        assert actual == []
        mock_flag_broker.load_flags.assert_called_once_with()
