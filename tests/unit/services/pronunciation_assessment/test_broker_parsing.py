"""Pure tests for the broker's SDK-result parsing helpers -- no Azure call, no network."""

from types import SimpleNamespace as NS

import pytest

from api.brokers.pronunciation_assessment.pronunciation_assessment_broker import _pcm_from_wav, parse_assessment


def _sdk_result(**overrides):
    base = dict(
        accuracy_score=91.0,
        fluency_score=82.0,
        completeness_score=100.0,
        pronunciation_score=88.5,
        prosody_score=None,
        words=[
            NS(word="perro", accuracy_score=90.0, error_type="None", phonemes=[NS(phoneme="p", accuracy_score=95.0)]),
            NS(word="gato", accuracy_score=40.0, error_type="Mispronunciation", phonemes=[]),
        ],
    )
    base.update(overrides)
    return NS(**base)


class TestParseAssessment:

    def test_should_map_scores_words_and_phonemes(self):
        result = parse_assessment(_sdk_result())

        assert (result.accuracy_score, result.fluency_score) == (91.0, 82.0)
        assert (result.completeness_score, result.pronunciation_score) == (100.0, 88.5)
        assert result.prosody_score is None
        assert [w.word for w in result.words] == ["perro", "gato"]
        assert result.words[0].phonemes[0].phoneme == "p"
        assert result.words[0].phonemes[0].accuracy_score == 95.0
        assert result.words[1].error_type == "Mispronunciation"

    def test_should_tolerate_missing_words_and_phonemes_and_word_score(self):
        # SDK leaves these attributes unset (AttributeError) when Azure omits them
        no_score_word = NS(word="uno", error_type="Omission")
        result = parse_assessment(_sdk_result(words=[no_score_word]))

        assert result.words[0].accuracy_score is None
        assert result.words[0].phonemes == []
        assert result.words[0].error_type == "Omission"

        no_words = _sdk_result()
        del no_words.words
        assert parse_assessment(no_words).words == []

    def test_should_pass_prosody_through_when_present(self):
        assert parse_assessment(_sdk_result(prosody_score=77.0)).prosody_score == 77.0

    def test_should_raise_when_overall_scores_missing(self):
        with pytest.raises(RuntimeError):
            parse_assessment(NS())


class TestPcmFromWav:

    def test_should_strip_riff_header_up_to_data_chunk(self):
        header = b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x10\x00\x00\x00" + b"\x00" * 16
        wav = header + b"data\x04\x00\x00\x00" + b"\x01\x02\x03\x04"

        assert _pcm_from_wav(wav) == b"\x01\x02\x03\x04"

    def test_should_raise_when_no_data_chunk(self):
        with pytest.raises(ValueError):
            _pcm_from_wav(b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x00" * 20)
