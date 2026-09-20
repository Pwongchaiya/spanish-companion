"""Validation checks for IngestionQueueService.

Same batched-errors shape as TopicCoveredServiceValidations: each public
method's checks collect into one InvalidIngestionQueueException reporting
every failing field. `topic` must be a key of rag/data/topics.py TOPICS
(api -> rag import, the permitted direction).
"""

from api.models.foundations.ingestion_queue.exceptions import InvalidIngestionQueueException
from rag.data.topics import TOPICS

_TOPIC_KEYS = frozenset(key for key, _ in TOPICS)
VALID_STATUSES = ("pending", "ingested", "dismissed")


class IngestionQueueServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input doesn't pass checks. See ingestion_queue_service_exceptions.py
    for how it gets wrapped and logged before leaving the service.
    """

    def _validate_ingestion_queue_on_create(self, topic: str | None, weak_verdict_count: int | None) -> None:
        self._validate(
            (topic not in _TOPIC_KEYS, "topic", "Topic must be a key of the RAE topic list"),
            (self._is_negative(weak_verdict_count), "weak_verdict_count", "Weak verdict count must be >= 0"),
        )

    def _validate_ingestion_queue_on_update(
        self, queue_id: int | None, weak_verdict_count: int | None, status: str | None
    ) -> None:
        self._validate(
            (queue_id is None or queue_id <= 0, "queue_id", "Queue id is required"),
            (self._is_negative(weak_verdict_count), "weak_verdict_count", "Weak verdict count must be >= 0"),
            (status not in VALID_STATUSES, "status", "Status must be pending, ingested or dismissed"),
        )

    @staticmethod
    def _is_negative(value: int | None) -> bool:
        return value is None or value < 0

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidIngestionQueueException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
