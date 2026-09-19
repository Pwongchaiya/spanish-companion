"""Leaf dependency exception raised when an IPronunciationResultBroker call fails."""

from api.errors import ApiError


class FailedPronunciationResultStorageException(ApiError):
    """Raised when insert_pronunciation_result()/select_all_pronunciation_results()
    raises any SQLAlchemyError. No unique constraint on `pronunciation_result`,
    so no AlreadyExists/DependencyValidation tier (same as session_log_entry).

    Leaf exception -- always caught and wrapped into
    PronunciationResultDependencyException before leaving the service.
    """
