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


def is_dialect_legit(said: str, variant: SpanishVariant) -> bool:
    """True if `said` contains a form that is correct in `variant`.

    ponytail: token match on the whole utterance, so a genuine error sitting
    next to a legit form in the same sentence is also dropped; under-flagging
    is the accepted direction (see the flag-emission note in
    voice_conversation_service.py). Upgrade path: match only the tokens that
    differ between `said` and `corrected`.
    """
    tokens = set(re.findall(r"\w+", said.lower()))
    return not tokens.isdisjoint(variant.legit_forms)


if __name__ == "__main__":
    assert get_variant(None) is get_variant("nonsense") is get_variant("neutral")
    assert is_dialect_legit("Vos tenés razón", get_variant("rioplatense"))
    assert not is_dialect_legit("Vos tenés razón", get_variant("neutral"))
    assert not is_dialect_legit("Yo soy cansado", get_variant("rioplatense"))
    assert set(VARIANT_KEYS) == {"neutral", "castilian", "rioplatense", "mexican"}
    print("OK")
