"""Adaptive-difficulty lookup table: CEFR estimate -> prompt guidance (D6).

Sibling of _pressure.py, same shape: frozen dataclass table + getter +
assert-based __main__ self-check. Read by the composition root
(api/exposers/voice_conversation.py), which passes the learner's stored
LearnerProfile.cefr_estimate. Unknown/missing/empty estimates yield no
block, so a bot with no estimate behaves exactly as before this feature.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DifficultyLevel:
    prompt_block: str


_LEVELS = {
    "A1": DifficultyLevel(
        "The learner is roughly CEFR A1: use only very common words, short present-tense sentences, "
        "and speak slowly and simply. Explain any new word briefly in English."
    ),
    "A2": DifficultyLevel(
        "The learner is roughly CEFR A2: use everyday vocabulary, simple sentences, and mostly present "
        "and simple past tenses. Avoid idioms and long subordinate clauses."
    ),
    "B1": DifficultyLevel(
        "The learner is roughly CEFR B1: use a moderate range of vocabulary, connected sentences, and "
        "common tenses including the future and imperfect. Introduce the occasional new word from context."
    ),
    "B2": DifficultyLevel(
        "The learner is roughly CEFR B2: use varied vocabulary, common idioms, and complex sentences "
        "including the subjunctive. Speak at a natural pace."
    ),
    "C1": DifficultyLevel(
        "The learner is roughly CEFR C1: use rich, nuanced vocabulary, idiomatic expressions, and "
        "sophisticated grammar at a natural native pace."
    ),
    "C2": DifficultyLevel(
        "The learner is roughly CEFR C2: speak as you would with an educated native speaker, with "
        "full idiomatic range, register shifts, and subtle nuance."
    ),
}


def get_difficulty_block(cefr_estimate: Optional[str]) -> str:
    """Prompt block for a CEFR level ('' for None/empty/unknown). Case and
    surrounding whitespace are ignored."""
    level = _LEVELS.get((cefr_estimate or "").strip().upper())
    return level.prompt_block if level else ""


if __name__ == "__main__":
    assert "A1" in get_difficulty_block(" a1 ")
    assert get_difficulty_block("C2") != get_difficulty_block("B1")
    assert get_difficulty_block(None) == ""
    assert get_difficulty_block("") == ""
    assert get_difficulty_block("D9") == ""
    print("OK")
