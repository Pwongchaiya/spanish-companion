"""Leaf dependency exception raised when an IPersonaBroker call fails."""

from api.errors import ApiError


class FailedPersonaStorageException(ApiError):
    """Raised when any IPersonaBroker call raises a SQLAlchemyError other than
    a unique-constraint IntegrityError (those become
    AlreadyExistsPersonaException).

    Leaf exception -- always caught and wrapped into
    PersonaDependencyException before leaving the service.
    """
