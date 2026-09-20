"""RAE grammar topics and their corresponding URLs — the corpus source list.

Extracted from rag/exposers/ingestion.py (2026-09-18, Phase 2 roadmap item
F1) so a lightweight consumer (ProgressOrchestrationService's corpus
coverage map) can read the topic list without importing the ingestion CLI
module, which pulls in requests/BeautifulSoup and the embedding-model
broker class at import time.
"""

TOPICS: list[tuple[str, str]] = [
    (
        "preterite-vs-imperfect",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/tiempos-verbales-del-modo-indicativo/el-pret%C3%A9rito-perfecto-simple-cant%C3%A9-la-oposici%C3%B3n-cant%C3%A9-he-cantado",  # noqa: E501
    ),
    (
        "preterite-vs-imperfect",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/tiempos-verbales-del-modo-indicativo/el-pret%C3%A9rito-imperfecto-cantaba-la-oposici%C3%B3n-cant%C3%A9-cantaba",  # noqa: E501
    ),
    (
        "ser-vs-estar",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-atributo/el-atributo-en-las-oraciones-copulativas/atributos-con-ser-y-estar",  # noqa: E501
    ),
    (
        "subjunctive-basics",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/modo-y-subordinaci%C3%B3n/introducci%C3%B3n",
    ),
    (
        "subjunctive-basics",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/tiempos-verbales-del-modo-subjuntivo/caracter%C3%ADsticas-generales",  # noqa: E501
    ),
    # Added 2026-09-10 per the RAG explanation quality gap diagnosis: the live
    # flagging prompt (api/data/prompts/voice_conversation_system.txt) emits
    # "gender agreement" as a category, but no corpus topic covered it before
    # this -- CategoryBoostFilter's own docstring documented the gap
    # ("correctly declines to boost 'gender agreement' ... which no corpus
    # topic covers"). "vocabulary" (the prompt's other uncovered category)
    # deliberately stays uncovered: it names wrong word choices, not a single
    # grammar rule RAE publishes one page on, so MaxDistanceFilter correctly
    # returning [] for it is the right outcome, not a gap to paper over.
    (
        "gender-agreement",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-g%C3%A9nero/g%C3%A9nero-concordancia-flexi%C3%B3n-y-sexo",  # noqa: E501
    ),
    # Added 2026-09-19 (F2 follow-up): common A2-B1 error areas the flag prompt
    # doesn't name but the learner hits. URLs verified fetchable via
    # fetch_page_text with real content. The first two are RAE's "El buen uso
    # del español", not the Nueva gramática básica the rest use.
    (
        "por-vs-para",
        "https://www.rae.es/buen-uso-espa%C3%B1ol/las-preposiciones-por-y-para",
    ),
    (
        "articles",
        "https://www.rae.es/buen-uso-espa%C3%B1ol/el-art%C3%ADculo-clases-y-usos",
    ),
    (
        "object-pronouns",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/complemento-directo-complemento-indirecto-complemento-de-r%C3%A9gimen/el-complemento-directo-cd/propiedades-gramaticales-del-complemento-directo",  # noqa: E501
    ),
    (
        "object-pronouns",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/complemento-directo-complemento-indirecto-complemento-de-r%C3%A9gimen/el-complemento-indirecto-ci/propiedades-gramaticales-del-complemento-indirecto",  # noqa: E501
    ),
]
