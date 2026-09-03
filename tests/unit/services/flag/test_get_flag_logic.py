"""Unit tests for FlagService.get_flag() -- happy path.

See test_get_flag_exceptions.py for the not-found and broker-failure paths.
"""


class TestFlagServiceGetFlag:

    def test_should_return_matching_flag_when_flag_id_exists(self, service, mock_flag_broker, make_flag):
        # given
        target = make_flag("flag-2")
        mock_flag_broker.load_flags.return_value = [make_flag("flag-1"), target]

        # when
        actual = service.get_flag("flag-2")

        # then
        assert actual == target
        mock_flag_broker.load_flags.assert_called_once_with()
