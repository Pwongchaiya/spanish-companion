"""Input validation: every rejection happens before the broker is touched,
asserted explicitly on call_count."""

import pytest

from api.models.foundations.pronunciation_result.exceptions import (
    InvalidPronunciationResultException,
    PronunciationResultValidationException,
)


def _assert_rejected(service, broker, result, field):
    with pytest.raises(PronunciationResultValidationException) as caught:
        service.create_pronunciation_result(result)

    assert isinstance(caught.value.inner_exception, InvalidPronunciationResultException)
    assert field in caught.value.inner_exception.errors
    assert broker.insert_pronunciation_result.call_count == 0


class TestCreateValidation:

    def test_should_reject_none_result(self, service, mock_pronunciation_result_broker):
        _assert_rejected(service, mock_pronunciation_result_broker, None, "result")

    @pytest.mark.parametrize("bad_text", [None, "", "   ", 5])
    def test_should_reject_blank_reference_text(self, service, mock_pronunciation_result_broker, make_result, bad_text):
        _assert_rejected(
            service, mock_pronunciation_result_broker, make_result(reference_text=bad_text), "reference_text"
        )

    @pytest.mark.parametrize("bad_locale", [None, "", "  "])
    def test_should_reject_blank_locale(self, service, mock_pronunciation_result_broker, make_result, bad_locale):
        _assert_rejected(service, mock_pronunciation_result_broker, make_result(locale=bad_locale), "locale")

    @pytest.mark.parametrize("field", ["accuracy_score", "fluency_score", "completeness_score", "pronunciation_score"])
    @pytest.mark.parametrize("bad_score", [None, -0.1, 100.1, float("nan"), float("inf"), "90", True])
    def test_should_reject_invalid_required_score(
        self, service, mock_pronunciation_result_broker, make_result, field, bad_score
    ):
        _assert_rejected(service, mock_pronunciation_result_broker, make_result(**{field: bad_score}), field)

    @pytest.mark.parametrize("bad_score", [-1, 101, float("nan"), "70"])
    def test_should_reject_invalid_prosody_score_when_present(
        self, service, mock_pronunciation_result_broker, make_result, bad_score
    ):
        _assert_rejected(
            service, mock_pronunciation_result_broker, make_result(prosody_score=bad_score), "prosody_score"
        )

    @pytest.mark.parametrize("bad_words", [None, {"word": "x"}, "[]", ("a",)])
    def test_should_reject_non_list_words_json(self, service, mock_pronunciation_result_broker, make_result, bad_words):
        _assert_rejected(service, mock_pronunciation_result_broker, make_result(words_json=bad_words), "words_json")

    def test_should_reject_non_datetime_created_at(self, service, mock_pronunciation_result_broker, make_result):
        _assert_rejected(service, mock_pronunciation_result_broker, make_result(created_at="2026-01-02"), "created_at")

    def test_should_report_every_failing_field_at_once(self, service, mock_pronunciation_result_broker, make_result):
        with pytest.raises(PronunciationResultValidationException) as caught:
            service.create_pronunciation_result(make_result(reference_text="", accuracy_score=-1, locale=" "))

        assert set(caught.value.inner_exception.errors) == {"reference_text", "accuracy_score", "locale"}
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 0
