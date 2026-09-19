"""Catch/wrap/log helpers for SessionLogEntryService.

Mirrors UserProfileService.Exceptions.cs's dispatch shape (NL.Core.Users,
Services/Foundations/UserProfiles/UserProfileService.Exceptions.cs) via the
TopicCoveredServiceExceptions precedent: a specific-exception-type dispatch
table, not a flat 3-bucket catch-all. `_try_catch` returns fn()'s value
since every public method here produces a SessionLogEntry or a list of them.

Three tiers only -- Validation, Dependency, catch-all Service. There is no
DependencyValidation tier because `session_log` has no unique constraint:
nothing this service does can produce a recoverable "row already exists",
so every SQLAlchemyError (IntegrityError included) lands on the dependency
catch-all. Per CLAUDE.md's Foundation waiver, the exception list is pinned
to what this feature can actually raise rather than the 9-class default.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import SQLAlchemyError

from api.models.foundations.session_log_entry.exceptions import (
    FailedSessionLogEntryStorageException,
    InvalidSessionLogEntryException,
    NotFoundSessionLogEntryException,
    SessionLogEntryDependencyException,
    SessionLogEntryServiceException,
    SessionLogEntryValidationException,
)

T = TypeVar("T")


class SessionLogEntryServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidSessionLogEntryException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundSessionLogEntryException as e:
            raise self._create_and_log_validation_exception(e) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedSessionLogEntryStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> SessionLogEntryValidationException:
        validation_exception = SessionLogEntryValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> SessionLogEntryDependencyException:
        dependency_exception = SessionLogEntryDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> SessionLogEntryServiceException:
        service_exception = SessionLogEntryServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
