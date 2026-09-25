"""Unit tests for FlagService.get_session_flags() -- happy paths.

Returns None (not []) when the broker has no snapshot for this session --
"no snapshot yet" and "snapshot with zero flags" are different callers'
concerns, see session_replay_service.py's fallback logic.
"""


class TestFlagServiceGetSessionFlags:

    def test_should_return_broker_flags_when_a_snapshot_exists(self, service, mock_flag_broker, make_flag):
        # given
        flags = [make_flag("flag-1"), make_flag("flag-2")]
        mock_flag_broker.get_session_flags.return_value = flags

        # when
        actual = service.get_session_flags(4)

        # then
        assert actual == flags
        mock_flag_broker.get_session_flags.assert_called_once_with(4)

    def test_should_return_none_when_no_snapshot_exists_for_the_session(self, service, mock_flag_broker):
        # given
        mock_flag_broker.get_session_flags.return_value = None

        # when
        actual = service.get_session_flags(4)

        # then
        assert actual is None
        mock_flag_broker.get_session_flags.assert_called_once_with(4)
