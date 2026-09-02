"""Ingestion CLI — hand-written, no agent, per CLAUDE.md's Phase 2
Layer-Agent Mapping (not worth the waivers for ~20 lines of argparse).

    python -m rag.exposers.ingestion

Fetches each RAE grammar page, hands the extracted text to
IngestionService, and prints a per-topic row count. Fetching (requests +
BeautifulSoup) lives here rather than in IngestionService so the service
stays a pure text -> rows operation.

Known limitation: re-running this against an already-populated corpus
inserts duplicate rows — ChunkRepositoryBroker has no read/exists method
to dedupe against prior runs (see
rag/services/orchestrations/ingestion/ingestion_service.py's docstring).
At MVP scale (3-5 topics), the fix is re-running the Alembic migration
(drops and recreates the table) before re-ingesting, not a code change.
"""

import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
from rag.services.foundations.chunk_repository import ChunkRepositoryService
from rag.services.foundations.embedding_model import EmbeddingModelService
from rag.services.orchestrations.ingestion import IngestionService

load_dotenv()

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))

# RAE grammar topics and their corresponding URLs — same corpus as Phase 1
# (rag/ingest.py's TOPICS), carried forward unchanged.
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
]


def fetch_page_text(url: str) -> str:
    """Fetch a RAE page and extract its visible main-content text.

    Unchanged from Phase 1's rag/ingest.py:fetch_page_text — working
    extraction logic, no reason to change it in a clean rewrite.
    """
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    content = soup.find("main") or soup.find("article") or soup.body or soup
    text = content.get_text()
    text = "\n".join(line for line in text.split("\n") if line.strip())
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(lines).strip()


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    chunk_repository_service = ChunkRepositoryService(
        SqlAlchemyChunkRepositoryBroker(connection_string=database_url)
    )
    embedding_model_service = EmbeddingModelService(SentenceTransformerEmbeddingModelBroker())
    service = IngestionService(chunk_repository_service, embedding_model_service)

    for topic, url in TOPICS:
        try:
            text = fetch_page_text(url)
        except requests.RequestException as e:
            print(f"SKIP {topic} ({url}): fetch failed — {e}")
            continue

        count = service.ingest_topic(topic, url, text)
        print(f"{topic}: {count} chunks ({url})")


if __name__ == "__main__":
    main()
