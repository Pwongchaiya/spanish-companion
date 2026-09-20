"""Ingestion-queue CLI (roadmap F2) -- hand-written, no agent, same style as
api/exposers/progress_digest.py.

    python -m api.exposers.ingestion_queue            # list pending topics
    python -m api.exposers.ingestion_queue --ingest   # ingest them, mark 'ingested'

A topic is pending once Review has recorded INGESTION_QUEUE_THRESHOLD (default 3)
weak grounding verdicts against it. Lives in api/ because the queue table is
api's; it reuses rag's fetch_page_text + IngestionOrchestrationService
(api -> rag, never the reverse).

Known limitation, inherited from rag/exposers/ingestion.py: ChunkRepositoryBroker
has no exists/delete method, so re-ingesting a topic that already has chunks
inserts duplicate rows.
"""

import sys
from typing import Callable

from dotenv import load_dotenv

from api.brokers.ingestion_queue import SqlAlchemyIngestionQueueBroker
from api.brokers.logging import StdlibLoggingBroker
from api.services.foundations.ingestion_queue import IngestionQueueService
from api.services.processings.ingestion_queue import IIngestionQueueProcessingService, IngestionQueueProcessingService

load_dotenv()


def ingest_pending(
    queue: IIngestionQueueProcessingService,
    threshold: int,
    ingest_topic: Callable[[str], bool],
    dry_run: bool,
) -> list[str]:
    """Topics handled. `ingest_topic` returns True on success (only then is the
    topic marked ingested); dry_run just lists."""
    handled = []
    for row in queue.list_pending(threshold):
        if dry_run:
            print(f"{row.topic}: {row.weak_verdict_count} weak verdicts (last {row.last_flagged_at:%Y-%m-%d})")
            handled.append(row.topic)
        elif ingest_topic(row.topic):
            queue.mark_ingested(row.topic)
            handled.append(row.topic)
    return handled


def main() -> None:
    import os

    from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
    from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
    from rag.brokers.logging import StdlibLoggingBroker as RagLoggingBroker
    from rag.data.topics import TOPICS
    from rag.exposers.ingestion import fetch_page_text
    from rag.services.foundations.chunk_repository import ChunkRepositoryService
    from rag.services.foundations.embedding_model import EmbeddingModelService
    from rag.services.orchestrations.ingestion import IngestionOrchestrationService

    import requests

    database_url = os.environ["DATABASE_URL"]
    threshold = int(os.getenv("INGESTION_QUEUE_THRESHOLD", "3"))
    timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    logging_broker = StdlibLoggingBroker()
    queue = IngestionQueueProcessingService(
        IngestionQueueService(SqlAlchemyIngestionQueueBroker(database_url), logging_broker=logging_broker)
    )
    dry_run = "--ingest" not in sys.argv

    ingestion = None
    if not dry_run:
        rag_logging = RagLoggingBroker()
        ingestion = IngestionOrchestrationService(
            ChunkRepositoryService(
                SqlAlchemyChunkRepositoryBroker(connection_string=database_url), logging_broker=rag_logging
            ),
            EmbeddingModelService(SentenceTransformerEmbeddingModelBroker(), logging_broker=rag_logging),
            logging_broker=rag_logging,
        )

    def ingest_topic(topic: str) -> bool:
        for key, url in TOPICS:
            if key != topic:
                continue
            try:
                text = fetch_page_text(url, timeout)
            except requests.RequestException as e:
                print(f"SKIP {topic} ({url}): fetch failed -- {e}")
                return False
            print(f"{topic}: {ingestion.ingest_topic(topic, url, text)} chunks ({url})")
        return True

    handled = ingest_pending(queue, threshold, ingest_topic, dry_run)
    if not handled:
        print("Nothing pending at or above the threshold.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        from datetime import datetime
        from unittest.mock import Mock

        from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue

        now = datetime(2026, 1, 1)
        rows = [IngestionQueue(1, "ser-vs-estar", 3, "pending", now, now), IngestionQueue(2, "gender-agreement", 4, "pending", now, now)]
        fake = Mock()
        fake.list_pending.return_value = rows

        assert ingest_pending(fake, 3, lambda t: True, dry_run=True) == ["ser-vs-estar", "gender-agreement"]
        assert fake.mark_ingested.call_count == 0, "dry run must not mark anything"

        # only the topic whose ingest succeeded is marked
        assert ingest_pending(fake, 3, lambda t: t == "gender-agreement", dry_run=False) == ["gender-agreement"]
        fake.mark_ingested.assert_called_once_with("gender-agreement")
        print("ingestion_queue CLI self-check passed")
    else:
        main()
