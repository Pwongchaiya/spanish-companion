"""Tests for api.brokers.bot_process.SubprocessBotProcessBroker.

Per test-broker-skill.md, brokers wrap an external resource (here, an OS
process, not a database) and are not unit-tested with mocks — subprocess.Popen
is the boundary itself, so these run real (short-lived, stdlib-only)
subprocesses instead. No mic, Azure credentials, or the not-yet-built
voice_conversation controller module required.

The broker exposes raw primitives only (start/send_graceful_signal/
terminate/kill/wait/is_running) — the graceful-then-kill escalation policy
belongs to ConversationSessionService, built next, so it is not tested here.
"""

import subprocess
import sys

import pytest

from api.brokers.bot_process import SubprocessBotProcessBroker

SLEEP_COMMAND = [sys.executable, "-c", "import time; time.sleep(30)"]
WAIT_TIMEOUT_SECONDS = 5  # well below SLEEP_COMMAND's duration, so a dishonoured
# signal (process still alive) raises TimeoutExpired instead of the natural
# sleep-exit happening to coincide with the wait deadline and passing anyway.


@pytest.fixture
def broker():
    broker = SubprocessBotProcessBroker(command=SLEEP_COMMAND)
    yield broker
    if broker.is_running():  # cleanup — no leftover process if a test fails mid-way
        broker.kill()
        broker.wait(WAIT_TIMEOUT_SECONDS)


class TestSubprocessBotProcessBroker:

    def test_should_not_be_running_when_never_started(self, broker):
        assert broker.is_running() is False

    def test_should_be_running_when_started(self, broker):
        broker.start()

        assert broker.is_running() is True

    def test_should_not_be_running_when_graceful_signal_is_honoured(self, broker):
        broker.start()

        broker.send_graceful_signal()
        broker.wait(WAIT_TIMEOUT_SECONDS)

        assert broker.is_running() is False

    def test_should_not_be_running_when_killed(self, broker):
        broker.start()

        broker.kill()
        broker.wait(WAIT_TIMEOUT_SECONDS)

        assert broker.is_running() is False

    def test_should_raise_timeout_expired_when_wait_exceeds_deadline(self, broker):
        broker.start()

        with pytest.raises(subprocess.TimeoutExpired):
            broker.wait(0.01)
