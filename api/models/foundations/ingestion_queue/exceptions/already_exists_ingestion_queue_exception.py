"""Leaf exception raised when an ingestion_queue row for a topic already exists.

A race, not a broken system: Processing's find-by-topic check and
IngestionQueueService.create_ingestion_queue() aren't atomic, so the UNIQUE
constraint on `topic` is the backstop -- this is the leaf raised when it
fires. Same shape as AlreadyExistsTopicCoveredException; wrapped into
IngestionQueueDependencyValidationException before leaving the service.
"""

from api.errors import ApiError


class AlreadyExistsIngestionQueueException(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
