"""Unit tests for FlagService.save_flags() -- happy path.

See test_save_flags_exceptions.py for the broker-failure path.
"""


class TestFlagServiceSaveFlags:

    def test_should_save_full_list_when_called(self, service, mock_flag_broker, make_flag):
        # given
        flags = [make_flag("flag-1"), make_flag("flag-2")]

        # when
        service.save_flags(flags)

        # then
        mock_flag_broker.save_flags.assert_called_once_with(flags)

    def test_should_save_empty_list_when_called_with_no_flags(self, service, mock_flag_broker):
        # when
        service.save_flags([])

        # then
        mock_flag_broker.save_flags.assert_called_once_with([])
