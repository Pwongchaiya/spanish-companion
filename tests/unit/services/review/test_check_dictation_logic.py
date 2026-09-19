"""Unit tests for the pure dictation comparison (Phase 5 E2) -- happy/diff paths."""

import pytest

from api.models.orchestrations.review.dictation import WordDiff
from api.services.orchestrations.review._dictation import check_dictation


def statuses(typed: str, target: str) -> list:
    return [d.status for d in check_dictation(typed, target)]


class TestCheckDictationLogic:

    def test_should_match_ignoring_case_whitespace_and_edge_punctuation(self):
        assert statuses("  Yo   TENGO. ", "yo tengo") == ["ok", "ok"]

    def test_should_match_when_target_has_spanish_inverted_punctuation(self):
        assert statuses("como estas", "¿Cómo estás?") == ["accent", "accent"]

    def test_should_report_accent_difference_as_accent(self):
        assert check_dictation("el esta aqui", "él está aquí") == [
            WordDiff(target="él", typed="el", status="accent"),
            WordDiff(target="está", typed="esta", status="accent"),
            WordDiff(target="aquí", typed="aqui", status="accent"),
        ]

    def test_should_report_enye_dropped_as_accent(self):
        assert statuses("ano", "año") == ["accent"]

    def test_should_report_different_letters_as_spelling(self):
        assert check_dictation("yo tego", "yo tengo")[1] == WordDiff(target="tengo", typed="tego", status="spelling")

    def test_should_report_missing_word(self):
        assert check_dictation("yo", "yo tengo")[1] == WordDiff(target="tengo", typed="", status="missing")

    def test_should_report_extra_word(self):
        assert check_dictation("yo tengo mucho", "yo tengo")[2] == WordDiff(target="", typed="mucho", status="extra")

    def test_should_treat_precomposed_and_decomposed_accents_as_equal(self):
        assert statuses("está", "está") == ["ok"]


class TestCheckDictationValidation:

    @pytest.mark.parametrize("typed", ["", "   ", None, 5])
    def test_should_reject_blank_or_non_string_typed(self, typed):
        with pytest.raises(ValueError):
            check_dictation(typed, "yo tengo")

    @pytest.mark.parametrize("target", ["", "  ", None])
    def test_should_reject_blank_or_non_string_target(self, target):
        with pytest.raises(ValueError):
            check_dictation("yo tengo", target)
