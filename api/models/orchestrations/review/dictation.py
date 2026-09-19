"""Domain models for Review Mode's typed dictation-back exercise (Phase 5 E2).

Plain data-carriers, never persisted. `target` is an existing flag's
`corrected` text -- no new LLM call, no new DB field.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DictationExercise:
    flag_id: str
    target: str


@dataclass
class WordDiff:
    """One aligned word. `status`: ok | accent | spelling | missing | extra.

    `accent` = same letters once diacritics are stripped (orthography);
    `spelling` = different letters; `missing` = typed is ""; `extra` = target is "".
    """

    target: str
    typed: str
    status: str


@dataclass
class DictationResult:
    flag_id: str
    target: str
    typed_text: str
    matches: bool
    words: List[WordDiff]
