"""Pure typed-vs-target comparison for dictation-back. No LLM, no I/O."""

import unicodedata
from difflib import SequenceMatcher
from typing import List

from api.models.orchestrations.review.dictation import WordDiff

_EDGE_PUNCTUATION = " .,;:!?\"'()[]-¿¡…«»"


def _words(text: str) -> List[str]:
    # casefold + whitespace collapse via split(); edge punctuation stripped so
    # "Hola," == "hola". Accents are deliberately kept -- they are the point.
    return [w for w in (t.strip(_EDGE_PUNCTUATION) for t in text.casefold().split()) if w]


def _strip_accents(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", word) if unicodedata.category(c) != "Mn")


def _pair_status(target: str, typed: str) -> str:
    if unicodedata.normalize("NFC", target) == unicodedata.normalize("NFC", typed):
        return "ok"
    return "accent" if _strip_accents(target) == _strip_accents(typed) else "spelling"


def check_dictation(typed: str, target: str) -> List[WordDiff]:
    """Per-word alignment of `typed` against `target`; all "ok" means a match.

    Raises ValueError if either side is not a non-blank string.
    """
    if not isinstance(typed, str) or not typed.strip():
        raise ValueError("typed text must be a non-blank string")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("target text must be a non-blank string")
    t_words, y_words = _words(target), _words(typed)
    diffs: List[WordDiff] = []
    for _op, t1, t2, y1, y2 in SequenceMatcher(None, t_words, y_words, autojunk=False).get_opcodes():
        t_chunk, y_chunk = t_words[t1:t2], y_words[y1:y2]
        for i in range(max(len(t_chunk), len(y_chunk))):
            t = t_chunk[i] if i < len(t_chunk) else ""
            y = y_chunk[i] if i < len(y_chunk) else ""
            status = "missing" if not y else "extra" if not t else _pair_status(t, y)
            diffs.append(WordDiff(target=t, typed=y, status=status))
    return diffs
