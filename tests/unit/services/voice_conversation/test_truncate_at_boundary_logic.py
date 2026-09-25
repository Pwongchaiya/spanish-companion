"""Unit tests for the free function _truncate_at_boundary.

Persona memory summaries used to be hard-cut with summary[:max_chars],
slicing mid-word/mid-sentence. This prefers a clean break: last sentence
end within the limit (past ~half of it), else last whitespace, else a
hard cut when neither exists.
"""

from api.services.orchestrations.voice_conversation.voice_conversation_service import (
    _truncate_at_boundary,
)


class TestTruncateAtBoundary:
    def test_returns_text_unchanged_when_within_limit(self):
        assert _truncate_at_boundary("short text", 50) == "short text"

    def test_cuts_at_last_sentence_end_past_half_the_limit(self):
        text = "Marta likes coffee. She works at the cafe downtown and loves her job there."
        result = _truncate_at_boundary(text, 25)

        assert result == "Marta likes coffee."
        assert len(result) <= 25

    def test_falls_back_to_last_whitespace_when_no_sentence_end_in_range(self):
        text = "a very long run of words with no punctuation anywhere at all in it"
        result = _truncate_at_boundary(text, 20)

        assert result == "a very long run of"
        assert len(result) <= 20
        assert not result.endswith(" ")

    def test_hard_cuts_when_no_whitespace_or_sentence_end(self):
        text = "x" * 50
        result = _truncate_at_boundary(text, 20)

        assert result == "x" * 20
        assert len(result) == 20


if __name__ == "__main__":
    import subprocess
    import sys

    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
