"""Leaf validation exception raised when Foundation input checks fail."""

from api.errors import ApiError


class InvalidIngestionQueueException(ApiError):
    """Raised by create_ingestion_queue()/update_ingestion_queue() when one or
    more arguments fail a structural check: queue_id not a positive int,
    topic blank or not a key of rag/data/topics.py TOPICS, count negative,
    status not pending|ingested|dismissed.

    Batches every failing field into `errors` before raising, same
    UpsertDataList/ThrowIfContainsErrors shape as InvalidTopicCoveredException.

    Leaf exception -- always caught and wrapped into
    IngestionQueueValidationException before leaving IngestionQueueService.
    """

    def __init__(self) -> None:
        super().__init__("Ingestion queue is invalid, fix the errors and try again.")
        self.errors: dict[str, list[str]] = {}

    def upsert_data_list(self, field: str, message: str) -> None:
        self.errors.setdefault(field, []).append(message)

    def throw_if_contains_errors(self) -> None:
        if self.errors:
            raise self
