"""Leaf dependency exception raised when an IIngestionQueueBroker call fails."""

from api.errors import ApiError


class FailedIngestionQueueStorageException(ApiError):
    """Raised when select_all_ingestion_queue()/insert_ingestion_queue()/
    update_ingestion_queue() raises anything other than a uniquely-classified
    IntegrityError (unique-constraint violations become
    AlreadyExistsIngestionQueueException instead).

    Leaf exception -- always caught and wrapped into
    IngestionQueueDependencyException before leaving IngestionQueueService.
    """
