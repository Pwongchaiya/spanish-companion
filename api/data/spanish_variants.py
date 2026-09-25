"""Regional Spanish variant table -- roadmap D2.

One static table, read by both sides of the process boundary: the
composition root (voice id + prompt block, api/exposers/voice_conversation.py)
and the voice orchestrator (dialect-legit flag suppression,
voice_conversation_service.py). Same shape and resolution pattern as
_pressure.py: the chosen key crosses into the subprocess as SESSION_VARIANT.

`neutral` is the pre-D2 behaviour verbatim: no prompt block, no legit-form
suppression, and the voice comes from AZURE_TTS_VOICE (its old default).
Every other variant's voice can be overridden via AZURE_TTS_VOICE_<KEY>.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SpanishVariant:
    key: str
    label: str
    voice: str
    voice_env: str
    language: str  # pipecat Language member name
    prompt_block: str
    # Lowercase word tokens that are correct in this variant. A live error
    # flag whose `said` contains one is dropped (see is_dialect_legit).
    legit_forms: frozenset


DEFAULT_VARIANT = "neutral"

_NO_FLAG_NOTE = (
    " Forms that are normal in this variety are not mistakes: never flag them, "
    "and never correct the learner toward a different variety."
)

_VARIANTS = {
    "neutral": SpanishVariant(
        key="neutral",
        label="Neutral LatAm",
        voice="es-ES-XimenaMultilingualNeural",
        voice_env="AZURE_TTS_VOICE",
        language="ES_ES",
        prompt_block="",
        legit_forms=frozenset(),
    ),
    "castilian": SpanishVariant(
        key="castilian",
        label="Castilian",
        voice="es-ES-ArabellaMultilingualNeural",
        voice_env="AZURE_TTS_VOICE_CASTILIAN",
        language="ES_ES",
        prompt_block=(
            "Speak Castilian Spanish from Spain: use vosotros/vosotras with its verb forms "
            "(habláis, tenéis), vale, and Peninsular vocabulary (ordenador, coche, coger)." + _NO_FLAG_NOTE
        ),
        legit_forms=frozenset(
            "vosotros vosotras os vuestro vuestra vuestros vuestras habláis tenéis sois estáis coméis "
            "queréis podéis sabéis vale ordenador".split()
        ),
    ),
    "rioplatense": SpanishVariant(
        key="rioplatense",
        label="Rioplatense",
        voice="es-AR-ElenaNeural",
        voice_env="AZURE_TTS_VOICE_RIOPLATENSE",
        language="ES_AR",
        prompt_block=(
            "Speak Rioplatense Spanish from Argentina and Uruguay: use voseo (vos tenés, vos sos, "
            "querés, podés, vení), che, and local vocabulary (laburo, pibe, re)." + _NO_FLAG_NOTE
        ),
        legit_forms=frozenset(
            "vos sos tenés querés podés sabés hablás comés vivís vení decime mirá che laburo pibe piba "
            "boludo re".split()
        ),
    ),
    "mexican": SpanishVariant(
        key="mexican",
        label="Mexican",
        voice="es-MX-DaliaNeural",
        voice_env="AZURE_TTS_VOICE_MEXICAN",
        language="ES_MX",
        prompt_block=(
            "Speak Mexican Spanish: use ustedes, ahorita, mande, órale, and Mexican vocabulary "
            "(platicar, carro, chamba, padre, chido)." + _NO_FLAG_NOTE
        ),
        legit_forms=frozenset(
            "ahorita mande órale orale ándale andale platicar carro chamba chido padre güey wey".split()
        ),
    ),
}

VARIANT_KEYS = tuple(_VARIANTS)


def get_variant(key: Optional[str]) -> SpanishVariant:
    """Unknown or missing keys fall back to neutral -- a hand-started bot (no
    Flask, no SESSION_VARIANT env var) behaves exactly as before D2."""
    return _VARIANTS.get(key or DEFAULT_VARIANT, _VARIANTS[DEFAULT_VARIANT])


def is_dialect_legit(said: str, corrected: str, variant: SpanishVariant) -> bool:
    """True if the only tokens `said` has that `corrected` doesn't are
    themselves legit forms in `variant` -- i.e. the diff is dialect
    vocabulary, not a real mistake.

    Upgrade from the old whole-utterance token match: only the tokens that
    differ between `said` and `corrected` are checked now, so a genuine
    error sitting next to a legit form in the same sentence is kept.

    ponytail: said-only tokens must be a (non-empty) subset of legit_forms
    -- no said-token -> corrected-token mapping, so a real error whose
    *wrong* word happens to itself be legit-form vocabulary (e.g. voseo
    "sos" used where the real mistake is ser/estar, "sos" -> "estás") is
    still suppressed if that's the only differing token. Under-flagging is
    the accepted direction here; closing this needs a said-form ->
    standard-form mapping this table doesn't have.
    """
    said_tokens = set(re.findall(r"\w+", said.lower()))
    corrected_tokens = set(re.findall(r"\w+", corrected.lower()))
    said_only = said_tokens - corrected_tokens
    return bool(said_only) and said_only <= variant.legit_forms


if __name__ == "__main__":
    assert get_variant(None) is get_variant("nonsense") is get_variant("neutral")
    assert is_dialect_legit("Vos tenés razón", "Tú tienes razón", get_variant("rioplatense"))
    assert not is_dialect_legit("Vos tenés razón", "Tú tienes razón", get_variant("neutral"))
    assert not is_dialect_legit("Yo soy cansado", "Yo estoy cansado", get_variant("rioplatense"))
    # A genuine error next to a legit form is kept -- the old whole-utterance
    # match would have dropped this because "vos"/"tenés" appear anywhere in
    # `said`; now only the said/corrected diff ("soy" vs "estoy") is checked.
    assert not is_dialect_legit(
        "Vos tenés hambre y yo soy cansado", "Vos tenés hambre y yo estoy cansado", get_variant("rioplatense")
    )
    assert set(VARIANT_KEYS) == {"neutral", "castilian", "rioplatense", "mexican"}
    print("OK")
