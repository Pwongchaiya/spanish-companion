"""Static minimal-pair word list for the listening-discrimination drill
(roadmap item B6). Same "small in-repo constant" convention as rag/
exposers/ingestion.py's TOPICS list -- no table, no migration, just a
Python constant, per the "Ask Before Building" rule (no schema invented
for a static, never-written list).

Each pair is two genuinely distinct real Spanish words that differ by one
sound a learner commonly confuses. Frontend keeps its own copy of this
same list (frontend/src/data/minimalPairs.ts) -- duplicated rather than
served over a new endpoint, since it's static data the client needs at
render time regardless (ladder rung 1: no endpoint needed for a constant
both sides can just know).
"""

# Two families, both audibly distinct regardless of dialect (unlike b/v or
# ll/y, which are homophones in most Spanish accents and would make a bad
# listening drill):
#   - single "r" vs. trilled "rr"
#   - stress placement (which syllable is stressed changes the word)
MINIMAL_PAIRS: list[tuple[str, str]] = [
    ("pero", "perro"),  # but / dog
    ("caro", "carro"),  # expensive / cart
    ("pera", "perra"),  # pear / female dog
    ("coro", "corro"),  # choir / I run
    ("cero", "cerro"),  # zero / hill
    ("para", "parra"),  # for / grapevine
    ("foro", "forro"),  # forum / lining
    ("moro", "morro"),  # Moorish / snout
    ("papa", "papá"),  # potato / dad
    ("como", "cómo"),  # as, like / how
    ("hablo", "habló"),  # I speak / he spoke
    ("paso", "pasó"),  # step / it happened
]


if __name__ == "__main__":
    # ponytail: no test framework for a static data file -- assert-based
    # self-check per the global "leave one runnable check" rule. Run with
    # `python -m api.data.minimal_pairs`.
    assert len(MINIMAL_PAIRS) >= 10, "expected at least 10 minimal pairs"
    for word_a, word_b in MINIMAL_PAIRS:
        assert word_a != word_b, f"pair must be two distinct words: {(word_a, word_b)!r}"
        assert word_a.strip() and word_b.strip(), f"pair must have no blank word: {(word_a, word_b)!r}"
    assert len(set(MINIMAL_PAIRS)) == len(MINIMAL_PAIRS), "duplicate pair found"
    print(f"OK: {len(MINIMAL_PAIRS)} minimal pairs, all well-formed")
