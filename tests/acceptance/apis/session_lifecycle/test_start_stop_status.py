"""Acceptance tests for the session_lifecycle Flask blueprint -- full HTTP
round trip through a real ConversationSessionService.

Does NOT go through api.app.create_app() -- that hardcodes
SubprocessBotProcessBroker() pointed at the real pipecat voice bot with no
injection point, and touching api/app.py is out of scope for this dispatch.
Instead the Flask app is built manually here, wired to a real
SubprocessBotProcessBroker pointed at the same lightweight polling-subprocess
fixture command tests/integration/brokers/test_bot_process.py uses -- a real
(harmless) OS process, no mic, no Azure/Google credentials.
"""

import sys

import pytest
from flask import Flask

from api.brokers.bot_process import SubprocessBotProcessBroker
from api.controllers.session_lifecycle import make_session_lifecycle_blueprint
from api.services.session_lifecycle import ConversationSessionService

WAIT_TIMEOUT_SECONDS = 5  # mirrors tests/integration/brokers/test_bot_process.py


@pytest.fixture
def broker(tmp_path):
    # Same fixture command pattern as test_bot_process.py's `broker` fixture:
    # polls for the stop-flag file send_graceful_signal() touches, so /stop
    # exercises the real graceful-shutdown contract instead of a plain sleep.
    stop_signal_path = tmp_path / "stop_signal"
    poll_command = [
        sys.executable,
        "-c",
        "import pathlib, time\n"
        f"p = pathlib.Path(r'{stop_signal_path}')\n"
        "while not p.exists():\n"
        "    time.sleep(0.05)\n",
    ]
    broker = SubprocessBotProcessBroker(command=poll_command, stop_signal_path=stop_signal_path)
    yield broker
    if broker.is_running():  # cleanup -- no leftover process if a test fails mid-way
        broker.kill()
        broker.wait(WAIT_TIMEOUT_SECONDS)


@pytest.fixture
def client(broker):
    app = Flask(__name__)
    service = ConversationSessionService(broker=broker)
    app.register_blueprint(make_session_lifecycle_blueprint(service))
    app.config["TESTING"] = True
    return app.test_client()


class TestSessionLifecycleAcceptance:

    def test_should_start_then_stop_a_real_session_end_to_end(self, client):
        # when -- start
        start_response = client.post("/start")

        # then -- started
        assert start_response.status_code == 200
        assert start_response.get_json()["running"] is True

        # when -- status
        status_response = client.get("/status")

        # then -- running
        assert status_response.status_code == 200
        assert status_response.get_json()["running"] is True

        # when -- start again
        second_start_response = client.post("/start")

        # then -- rejected, already running
        assert second_start_response.status_code == 409
        assert "error" in second_start_response.get_json()

        # when -- stop
        stop_response = client.post("/stop")

        # then -- stopped gracefully
        assert stop_response.status_code == 200
        stop_body = stop_response.get_json()
        assert stop_body["running"] is False
        assert stop_body["graceful"] is True

        # when -- status
        status_after_stop_response = client.get("/status")

        # then -- not running
        assert status_after_stop_response.status_code == 200
        assert status_after_stop_response.get_json()["running"] is False

        # when -- stop again
        second_stop_response = client.post("/stop")

        # then -- rejected, not running
        assert second_stop_response.status_code == 404
        assert "error" in second_stop_response.get_json()
