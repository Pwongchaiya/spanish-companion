"""Unit tests for FlagService.list_flags() -- pass-through.

No exceptions file: FlagBroker.load_flags() returns [] for a missing or
corrupt file by contract, and "no flags yet" is a normal state, so
list_flags() has no failure mode of its own to test. Deliberately NOT routed
through _try_catch -- see flag_service.py's docstring on this method.
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
