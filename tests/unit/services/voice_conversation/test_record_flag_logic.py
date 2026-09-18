"""Unit tests for the free function _record_flag (A7+B3, 2026-09-18).

A7: repeat flags for the same (category, said, corrected) within a session
collapse into one Flag with an incremented occurrence_count.
B3: orthography-channel flags are dropped before ever reaching session_flags
-- a spoken session can't legitimately produce one until E2 (dictation-back)
exists.
"""

from datetime import datetime
from unittest.mock import Mock

from api.brokers.logging import LoggingBroker
from api.models.foundations.flag import Flag
from api.services.orchestrations.voice_conversation.voice_conversation_service import _record_flag


def _parsed(**overrides):
    base = {"said": "yo soy tener", "corrected": "yo tengo", "category": "verb_conjugation", "channel": "grammar"}
    base.update(overrides)
    return base


class TestRecordFlag:
    def test_appends_new_flag(self):
        session_flags: list[Flag] = []

        _record_flag(session_flags, _parsed(), Mock(spec=LoggingBroker))

        assert len(session_flags) == 1
        assert session_flags[0].occurrence_count == 1
        assert session_flags[0].channel == "grammar"

    def test_repeat_of_same_mistake_increments_existing_instead_of_appending(self):
        session_flags = [
            Flag(
                id="existing",
                said="yo soy tener",
                corrected="yo tengo",
                category="verb_conjugation",
                timestamp=datetime.now(),
                channel="grammar",
                occurrence_count=1,
            )
        ]

        _record_flag(session_flags, _parsed(), Mock(spec=LoggingBroker))

        assert len(session_flags) == 1
        assert session_flags[0].id == "existing"
        assert session_flags[0].occurrence_count == 2

    def test_different_mistake_appends_separately(self):
        session_flags = [
            Flag(
                id="existing",
                said="yo soy tener",
                corrected="yo tengo",
                category="verb_conjugation",
                timestamp=datetime.now(),
            )
        ]

        _record_flag(session_flags, _parsed(said="ella es feliz", corrected="ella está feliz", category="ser_estar"), Mock(spec=LoggingBroker))

        assert len(session_flags) == 2

    def test_orthography_channel_is_dropped_not_appended(self):
        session_flags: list[Flag] = []
        logging_broker = Mock(spec=LoggingBroker)

        _record_flag(session_flags, _parsed(channel="orthography"), logging_broker)

        assert session_flags == []
        logging_broker.log_info.assert_called_once()


if __name__ == "__main__":
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
