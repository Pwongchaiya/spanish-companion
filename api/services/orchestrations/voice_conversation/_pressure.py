"""Pressure-dial lookup table: pace level -> TTS rate, idle-rescue timing,
and lexical-range prompt guidance (D5, decisions/feature-plan-D5-pressure-
dial-2026-09-18.md).

One table, one module, read by both sides of the process boundary --
the composition root (needs tts_rate + prompt_block,
api/exposers/voice_conversation.py) and this package's own orchestration
service (needs user_idle_timeout + rescue_line,
voice_conversation_service.py) -- avoiding duplication and a circular
import between them. Each side resolves SESSION_PRESSURE itself via its
own ConfigurationBroker; no new constructor parameter on either class.

VAD_STOP_SECS/VAD_CONFIDENCE (hardware-calibration knobs, see
voice_conversation_service.py's _setup()) are deliberately NOT driven by
this table -- coupling them to pressure would silently re-tune mic/room
calibration whenever the learner picks a pace.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PressureLevel:
    tts_rate: str
    user_idle_timeout: float
    rescue_line: str
    prompt_block: str


DEFAULT_LEVEL = "normal"

_LEVELS = {
    "gentle": PressureLevel(
        tts_rate="-15%",
        user_idle_timeout=6.0,
        rescue_line="Tómate tu tiempo. ¿Quieres que repita la pregunta?",
        prompt_block=(
            "Speak slowly and stick to simple, common vocabulary. Give the "
            "learner plenty of room to think before responding."
        ),
    ),
    "normal": PressureLevel(
        tts_rate="+0%",
        user_idle_timeout=4.0,
        rescue_line="¿Sigues ahí? Responde cuando quieras.",
        prompt_block="Speak at a natural conversational pace with everyday vocabulary.",
    ),
    "push": PressureLevel(
        tts_rate="+12%",
        # ponytail: 0 disables pipecat's idle-timeout event entirely (see
        # LLMUserAggregatorParams' docstring) -- push level never rescues,
        # by design (plan doc §5.3): the learner sits in silence and finds
        # their own way out.
        user_idle_timeout=0,
        rescue_line="",
        prompt_block=(
            "Speak at a brisk natural pace and reach for broader vocabulary "
            "and idioms -- push the learner, don't simplify for them."
        ),
    ),
}


def get_pressure_level(level: Optional[str]) -> PressureLevel:
    """Look up a pressure level by its /start-body token. Unknown or missing
    values fall back to `normal` -- a hand-started bot (no Flask, no
    SESSION_PRESSURE env var) behaves exactly as it did before this feature
    existed."""
    return _LEVELS.get(level or DEFAULT_LEVEL, _LEVELS[DEFAULT_LEVEL])


if __name__ == "__main__":
    assert get_pressure_level("gentle").tts_rate == "-15%"
    assert get_pressure_level("push").user_idle_timeout == 0
    assert get_pressure_level(None) is get_pressure_level("normal")
    assert get_pressure_level("nonsense") is get_pressure_level("normal")
    print("OK")
