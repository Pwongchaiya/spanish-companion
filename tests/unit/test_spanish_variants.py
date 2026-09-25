"""Unit tests for D2's regional-variant table: lookup fallback and the
dialect-legit token guard. Pure data, no mocks."""

import pytest

from api.data.spanish_variants import VARIANT_KEYS, get_variant, is_dialect_legit


class TestGetVariant:

    def test_should_expose_the_four_variants(self):
        assert set(VARIANT_KEYS) == {"neutral", "castilian", "rioplatense", "mexican"}

    @pytest.mark.parametrize("value", [None, "", "klingon"])
    def test_should_fall_back_to_neutral_for_missing_or_unknown(self, value):
        assert get_variant(value) is get_variant("neutral")

    def test_neutral_should_preserve_pre_d2_behaviour(self):
        neutral = get_variant("neutral")
        assert neutral.prompt_block == ""
        assert neutral.legit_forms == frozenset()
        assert neutral.voice_env == "AZURE_TTS_VOICE"

    @pytest.mark.parametrize("key", ["castilian", "rioplatense", "mexican"])
    def test_non_default_variants_should_carry_voice_prompt_and_legit_forms(self, key):
        variant = get_variant(key)
        assert variant.voice.startswith("es-")
        assert variant.prompt_block
        assert variant.legit_forms


class TestIsDialectLegit:

    @pytest.mark.parametrize(
        "key, said, corrected",
        [
            ("rioplatense", "Vos tenés razón", "Tú tienes razón"),
            ("castilian", "Vosotros habláis rápido", "Ustedes hablan rápido"),
            ("mexican", "Ahorita voy", "Ya voy"),
        ],
    )
    def test_should_be_true_for_a_form_legit_in_that_variant(self, key, said, corrected):
        assert is_dialect_legit(said, corrected, get_variant(key))

    def test_should_be_false_for_the_same_form_in_another_variant(self):
        assert not is_dialect_legit("Vos tenés razón", "Tú tienes razón", get_variant("mexican"))
        assert not is_dialect_legit("Vos tenés razón", "Tú tienes razón", get_variant("neutral"))

    def test_should_be_false_for_a_genuine_error(self):
        assert not is_dialect_legit("Yo soy cansado", "Yo estoy cansado", get_variant("rioplatense"))

    def test_should_be_false_for_genuine_error_next_to_a_legit_form(self):
        """A real error sitting next to dialect vocabulary is no longer
        dropped -- only the said/corrected diff is checked now."""
        assert not is_dialect_legit(
            "Vos tenés hambre y yo soy cansado", "Vos tenés hambre y yo estoy cansado", get_variant("rioplatense")
        )
