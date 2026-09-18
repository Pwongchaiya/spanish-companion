"""Ingestion CLI — hand-written, no agent, per CLAUDE.md's Phase 2
Layer-Agent Mapping (not worth the waivers for ~20 lines of argparse).

    python -m rag.exposers.ingestion

Fetches each RAE grammar page, hands the extracted text to
IngestionOrchestrationService, and prints a per-topic row count. Fetching (requests +
BeautifulSoup) lives here rather than in IngestionOrchestrationService so the service
stays a pure text -> rows operation.

Known limitation: re-running this against an already-populated corpus
inserts duplicate rows — ChunkRepositoryBroker has no read/exists method
to dedupe against prior runs (see
rag/services/orchestrations/ingestion/ingestion_service.py's docstring).
At MVP scale (3-5 topics), the fix is re-running the Alembic migration
(drops and recreates the table) before re-ingesting, not a code change.
"""

import requests
from bs4 import BeautifulSoup

from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
from rag.brokers.configuration import EnvConfigurationBroker
from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
from rag.brokers.logging import StdlibLoggingBroker
from rag.data.topics import TOPICS
from rag.services.foundations.chunk_repository import ChunkRepositoryService
from rag.services.foundations.embedding_model import EmbeddingModelService
from rag.services.orchestrations.ingestion import IngestionOrchestrationService


def fetch_page_text(url: str, timeout_seconds: int) -> str:
    """Fetch a RAE grammar page and extract its grammar-body text.

    RAE's page has no semantic `<main>`/`<article>` tag — `soup.find("main")`
    matches nothing, so the original extraction fell back to `soup.body`,
    pulling in the "container diccionario" sidebar (dictionary search links,
    "También le interesará" news items) alongside the real grammar text.
    The actual grammar body lives in `<div id="resultados">`, confirmed by
    inspecting the ser-vs-estar page's DOM directly — every ingested topic
    is a RAE "gramática básica" page sharing this same template.
    """
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find(id="resultados") or soup.body or soup
    for tag in content.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    text = content.get_text()
    text = "\n".join(line for line in text.split("\n") if line.strip())
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(lines).strip()


def main() -> None:
    logging_broker = StdlibLoggingBroker()
    configuration_broker = EnvConfigurationBroker()
    request_timeout_seconds = int(configuration_broker.get("REQUEST_TIMEOUT_SECONDS", "15"))
    database_url = configuration_broker.require("DATABASE_URL")
    chunk_repository_service = ChunkRepositoryService(
        SqlAlchemyChunkRepositoryBroker(connection_string=database_url),
        logging_broker=logging_broker,
    )
    embedding_model_service = EmbeddingModelService(
        SentenceTransformerEmbeddingModelBroker(), logging_broker=logging_broker
    )
    service = IngestionOrchestrationService(chunk_repository_service, embedding_model_service, logging_broker=logging_broker)

    for topic, url in TOPICS:
        try:
            text = fetch_page_text(url, request_timeout_seconds)
        except requests.RequestException as e:
            print(f"SKIP {topic} ({url}): fetch failed — {e}")
            continue

        count = service.ingest_topic(topic, url, text)
        print(f"{topic}: {count} chunks ({url})")


def _selftest() -> None:
    """Assert-based check: fetch_page_text must pull only #resultados text,
    dropping sidebar/nav content sitting outside it -- the exact bug this
    function was fixed for (junk chunks in the ingested corpus)."""
    import unittest.mock as mock

    html = """
    <html><body>
      <nav>skip me</nav>
      <div class="container diccionario">
        <div class="row">
          <div class="col-xs-12 col-md-8">
            <div id="resultados"><p>Real grammar content.</p></div>
          </div>
          <div class="col-xs-12 col-md-4">Tambien le interesara: sidebar junk</div>
        </div>
      </div>
    </body></html>
    """
    fake_response = mock.Mock(text=html, raise_for_status=lambda: None)
    with mock.patch("requests.get", return_value=fake_response):
        text = fetch_page_text("http://example.invalid", timeout_seconds=1)
    assert text == "Real grammar content.", text
    assert "sidebar junk" not in text
    print("ok")


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
