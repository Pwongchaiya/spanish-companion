"""Leaf validation exception raised when an ingestion_queue row doesn't exist.

Raised by IngestionQueueService.update_ingestion_queue() when the broker
returns None for a missing queue_id. list_ingestion_queue() returns an empty
list rather than raising -- "no rows" isn't a not-found condition.
"""

from api.errors import ApiError


class NotFoundIngestionQueueException(ApiError):
    """Leaf exception -- always caught and wrapped into
    IngestionQueueValidationException before leaving IngestionQueueService.
    """

    def __init__(self) -> None:
        super().__init__("No ingestion_queue row exists for that lookup")
