"""Unit tests for the free function parse_flag (A7+B3, 2026-09-18).

Covers the new "channel" extraction: valid values pass through, missing or
out-of-vocabulary values default to "grammar" instead of dropping the whole
flag -- flag emission is prompt-compliance-only (see the ponytail note above
parse_flag), so a model that forgets "channel" shouldn't lose the flag.
"""

from unittest.mock import Mock

from api.brokers.logging import LoggingBroker
from api.services.orchestrations.voice_conversation.voice_conversation_service import parse_flag


def _logging_broker():
    return Mock(spec=LoggingBroker)


class TestParseFlag:
    def test_extracts_valid_channel(self):
        content = '{"said": "yo soy tener", "corrected": "yo tengo", "category": "verb_conjugation", "channel": "lexis"}'

        parsed = parse_flag(content, _logging_broker())

        assert parsed == {
            "said": "yo soy tener",
            "corrected": "yo tengo",
            "category": "verb_conjugation",
            "channel": "lexis",
        }

    def test_defaults_missing_channel_to_grammar(self):
        content = '{"said": "yo soy tener", "corrected": "yo tengo", "category": "verb_conjugation"}'

        parsed = parse_flag(content, _logging_broker())

        assert parsed["channel"] == "grammar"

    def test_defaults_unrecognized_channel_to_grammar(self):
        content = (
            '{"said": "yo soy tener", "corrected": "yo tengo", "category": "verb_conjugation", '
            '"channel": "not-a-real-channel"}'
        )

        parsed = parse_flag(content, _logging_broker())

        assert parsed["channel"] == "grammar"

    def test_returns_none_and_warns_on_malformed_json(self):
        logging_broker = _logging_broker()

        parsed = parse_flag("not json", logging_broker)

        assert parsed is None
        logging_broker.log_warning.assert_called_once()


if __name__ == "__main__":
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
