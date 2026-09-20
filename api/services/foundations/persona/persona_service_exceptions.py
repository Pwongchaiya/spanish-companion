"""Catch/wrap/log helpers for PersonaService.

Same dispatch shape as TopicCoveredServiceExceptions: Validation (invalid input
+ not found), DependencyValidation (unique-slug violation), Dependency
(any other SQLAlchemyError), catch-all Service.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.models.foundations.persona.exceptions import (
    AlreadyExistsPersonaException,
    FailedPersonaStorageException,
    InvalidPersonaException,
    NotFoundPersonaException,
    PersonaDependencyException,
    PersonaDependencyValidationException,
    PersonaServiceException,
    PersonaValidationException,
)

T = TypeVar("T")

# Postgres/pg8000 and sqlite unique-violation messages contain one of these
# phrases; NOT NULL and CHECK violations do not.
_UNIQUE_VIOLATION_MARKERS = ("unique constraint", "duplicate key")


class PersonaServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except (InvalidPersonaException, NotFoundPersonaException) as e:
            raise self._create_and_log_validation_exception(e) from e
        except IntegrityError as e:
            if self._is_unique_violation(e):
                already_exists = AlreadyExistsPersonaException("Persona already exists for this slug.")
                raise self._create_and_log_dependency_validation_exception(already_exists) from e
            raise self._create_and_log_dependency_exception(FailedPersonaStorageException(str(e))) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedPersonaStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    @staticmethod
    def _is_unique_violation(error: IntegrityError) -> bool:
        message = str(error.orig if error.orig is not None else error).lower()
        return any(marker in message for marker in _UNIQUE_VIOLATION_MARKERS)

    def _create_and_log_validation_exception(self, exception: Exception) -> PersonaValidationException:
        validation_exception = PersonaValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> PersonaDependencyException:
        dependency_exception = PersonaDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_dependency_validation_exception(
        self, exception: Exception
    ) -> PersonaDependencyValidationException:
        dependency_validation_exception = PersonaDependencyValidationException(inner_exception=exception)
        self._logging_broker.log_error(dependency_validation_exception)
        return dependency_validation_exception

    def _create_and_log_service_exception(self, exception: Exception) -> PersonaServiceException:
        service_exception = PersonaServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
