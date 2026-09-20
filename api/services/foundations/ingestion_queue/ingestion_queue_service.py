"""Foundation service for the ingestion_queue entity (roadmap F2).

Wraps IIngestionQueueBroker (api/brokers/ingestion_queue/) with input
validation only -- pure CRUD, no upsert, no find-by-topic (Processing's job).

Single broker dependency -> Foundation layer. Same shape as
TopicCoveredService: the concrete class is declared here, inheriting the
Validations/Exceptions mixins by name; each public method's entire body is an
inline closure passed to `_try_catch`. `update_ingestion_queue`'s None-check
is a business check on a normal return value, not exception handling.
"""

from datetime import datetime

from api.brokers.ingestion_queue.i_ingestion_queue_broker import IIngestionQueueBroker
from api.brokers.logging import LoggingBroker
from api.models.foundations.ingestion_queue.exceptions import NotFoundIngestionQueueException
from api.models.foundations.ingestion_queue.ingestion_queue import IngestionQueue
from api.services.foundations.ingestion_queue.i_ingestion_queue_service import IIngestionQueueService
from api.services.foundations.ingestion_queue.ingestion_queue_service_exceptions import (
    IngestionQueueServiceExceptions,
)
from api.services.foundations.ingestion_queue.ingestion_queue_service_validations import (
    IngestionQueueServiceValidations,
)


class IngestionQueueService(
    IngestionQueueServiceExceptions,
    IngestionQueueServiceValidations,
    IIngestionQueueService,
):
    """Owns IngestionQueue CRUD."""

    def __init__(
        self,
        ingestion_queue_broker: IIngestionQueueBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._ingestion_queue_broker = ingestion_queue_broker
        self._logging_broker = logging_broker

    def list_ingestion_queue(self) -> list[IngestionQueue]:
        def action() -> list[IngestionQueue]:
            return self._ingestion_queue_broker.select_all_ingestion_queue()

        return self._try_catch(action)

    def create_ingestion_queue(self, topic: str, weak_verdict_count: int, flagged_at: datetime) -> IngestionQueue:
        def action() -> IngestionQueue:
            self._validate_ingestion_queue_on_create(topic, weak_verdict_count)
            return self._ingestion_queue_broker.insert_ingestion_queue(topic, weak_verdict_count, flagged_at)

        return self._try_catch(action)

    def update_ingestion_queue(
        self, queue_id: int, weak_verdict_count: int, status: str, last_flagged_at: datetime
    ) -> IngestionQueue:
        def action() -> IngestionQueue:
            self._validate_ingestion_queue_on_update(queue_id, weak_verdict_count, status)
            maybe_row = self._ingestion_queue_broker.update_ingestion_queue(
                queue_id, weak_verdict_count, status, last_flagged_at
            )
            if maybe_row is None:
                raise NotFoundIngestionQueueException()
            return maybe_row

        return self._try_catch(action)
