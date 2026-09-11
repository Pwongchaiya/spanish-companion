"""Catch/wrap/log helpers for MistakePatternService.

Mirrors UserProfileService.Exceptions.cs's dispatch shape (NL.Core.Users,
Services/Foundations/UserProfiles/UserProfileService.Exceptions.cs:22-86):
a specific-exception-type dispatch table, not a flat 3-bucket catch-all.
`_try_catch` returns fn()'s value since every public method here produces a
MistakePattern or a list of them.

SQLAlchemy has no DuplicateKeyException-equivalent pre-classified type
(unlike EFxceptions, which NL.Core.Users relies on) -- IntegrityError covers
every constraint violation, so `_is_unique_violation` inspects the driver's
raw error text to tell "row already exists" (recoverable, a race between
Processing's find-by-category check and create()) apart from any other
integrity failure. Every other SQLAlchemyError (connection failures, etc.)
is the dependency-tier catch-all, mirroring SqlException/DbUpdateException
in the reference -- the broker does no wrapping of its own (pure I/O), so
classifying raw driver exceptions is this dispatch's job alone.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.models.foundations.mistake_pattern.exceptions import (
    AlreadyExistsMistakePatternException,
    InvalidMistakePatternException,
    MistakePatternDependencyException,
    MistakePatternDependencyValidationException,
    MistakePatternServiceException,
    FailedMistakePatternStorageException,
    MistakePatternValidationException,
    NotFoundMistakePatternException,
)

T = TypeVar("T")

# Postgres/pg8000's unique-violation message contains one of these phrases;
# NOT NULL, FOREIGN KEY, and CHECK violations do not.
_UNIQUE_VIOLATION_MARKERS = ("unique constraint", "duplicate key")


class MistakePatternServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidMistakePatternException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundMistakePatternException as e:
            raise self._create_and_log_validation_exception(e) from e
        except IntegrityError as e:
            if self._is_unique_violation(e):
                already_exists = AlreadyExistsMistakePatternException(
                    "Mistake pattern already exists for this profile and category."
                )
                raise self._create_and_log_dependency_validation_exception(already_exists) from e
            raise self._create_and_log_dependency_exception(FailedMistakePatternStorageException(str(e))) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedMistakePatternStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    @staticmethod
    def _is_unique_violation(error: IntegrityError) -> bool:
        message = str(error.orig if error.orig is not None else error).lower()
        return any(marker in message for marker in _UNIQUE_VIOLATION_MARKERS)

    def _create_and_log_validation_exception(self, exception: Exception) -> MistakePatternValidationException:
        validation_exception = MistakePatternValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> MistakePatternDependencyException:
        dependency_exception = MistakePatternDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_dependency_validation_exception(
        self, exception: Exception
    ) -> MistakePatternDependencyValidationException:
        dependency_validation_exception = MistakePatternDependencyValidationException(inner_exception=exception)
        self._logging_broker.log_error(dependency_validation_exception)
        return dependency_validation_exception

    def _create_and_log_service_exception(self, exception: Exception) -> MistakePatternServiceException:
        service_exception = MistakePatternServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
