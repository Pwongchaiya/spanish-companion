"""Unit test for api.app's Origin/Referer allowlist check.

Doesn't go through create_app() -- see
tests/acceptance/apis/session_lifecycle/test_start_stop_status.py's
docstring for why (hardcoded pipecat/Azure deps, no injection point).
_is_allowed_origin() is a pure function, so it's tested directly.
"""

from api.app import _is_allowed_origin

ALLOWED = frozenset({"http://localhost:5000", "http://localhost:5173"})


class TestIsAllowedOrigin:

    def test_should_allow_exact_origin_match(self):
        assert _is_allowed_origin("http://localhost:5000", ALLOWED) is True

    def test_should_allow_referer_with_path(self):
        assert _is_allowed_origin("http://localhost:5173/review", ALLOWED) is True

    def test_should_reject_suffix_bypass_of_allowed_origin(self):
        # regression: startswith() previously let this through because
        # "http://localhost:5000.evil.com" starts with the allowed
        # "http://localhost:5000"
        assert _is_allowed_origin("http://localhost:5000.evil.com", ALLOWED) is False

    def test_should_reject_port_prefix_bypass(self):
        # regression: startswith() previously let this through because
        # "http://localhost:51730" starts with the allowed
        # "http://localhost:5173"
        assert _is_allowed_origin("http://localhost:51730", ALLOWED) is False

    def test_should_reject_unrelated_origin(self):
        assert _is_allowed_origin("http://evil.com", ALLOWED) is False
