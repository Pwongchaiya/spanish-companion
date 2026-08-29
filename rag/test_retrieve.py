# MANUAL smoke check: only passes after running python rag/ingest.py to populate the chunks table

from rag.retrieve import retrieve


if __name__ == "__main__":
    result = retrieve("preterite vs imperfect")
    assert result is not None, "Expected non-None result for known query"
    assert result["topic"] == "preterite-vs-imperfect", (
        f"Expected topic 'preterite-vs-imperfect', got {result['topic']}"
    )
    print("Smoke test passed: retrieve() works and found preterite-vs-imperfect topic")
