"""Unit tests for FlagService.save_session_flags() -- happy path.

See test_save_session_flags_exceptions.py for the broker-failure path.
"""


class TestFlagServiceSaveSessionFlags:

    def test_should_save_session_flags_under_the_given_id_when_called(self, service, mock_flag_broker, make_flag):
        # given
        flags = [make_flag("flag-1"), make_flag("flag-2")]

        # when
        service.save_session_flags(4, flags)

        # then
        mock_flag_broker.save_session_flags.assert_called_once_with(4, flags)

    def test_should_save_empty_list_when_called_with_no_flags(self, service, mock_flag_broker):
        # when
        service.save_session_flags(4, [])

        # then
        mock_flag_broker.save_session_flags.assert_called_once_with(4, [])
