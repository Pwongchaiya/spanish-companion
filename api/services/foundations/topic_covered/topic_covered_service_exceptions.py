"""Catch/wrap/log helpers for TopicCoveredService.

Mirrors UserProfileService.Exceptions.cs's dispatch shape (NL.Core.Users,
Services/Foundations/UserProfiles/UserProfileService.Exceptions.cs:22-86)
via the MistakePatternServiceExceptions precedent: a specific-exception-type
dispatch table, not a flat 3-bucket catch-all. `_try_catch` returns fn()'s
value since every public method here produces a TopicCovered or a list of
them.

SQLAlchemy has no DuplicateKeyException-equivalent pre-classified type
(unlike EFxceptions, which NL.Core.Users relies on) — IntegrityError covers
every constraint violation, so `_is_unique_violation` inspects the driver's
raw error text to tell "row already exists" (recoverable, a race between
Processing's find-by-topic check and create_topic_covered()) apart from any
other integrity failure. Every other SQLAlchemyError (connection failures,
etc.) is the dependency-tier catch-all, mirroring SqlException/
DbUpdateException in the reference — the broker does no wrapping of its own
(pure I/O), so classifying raw driver exceptions is this dispatch's job
alone.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from api.models.foundations.topic_covered.exceptions import (
    AlreadyExistsTopicCoveredException,
    InvalidTopicCoveredException,
    FailedTopicCoveredStorageException,
    NotFoundTopicCoveredException,
    TopicCoveredDependencyException,
    TopicCoveredDependencyValidationException,
    TopicCoveredServiceException,
    TopicCoveredValidationException,
)

T = TypeVar("T")

# Postgres/pg8000's unique-violation message contains one of these phrases;
# NOT NULL, FOREIGN KEY, and CHECK violations do not.
_UNIQUE_VIOLATION_MARKERS = ("unique constraint", "duplicate key")


class TopicCoveredServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidTopicCoveredException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundTopicCoveredException as e:
            raise self._create_and_log_validation_exception(e) from e
        except IntegrityError as e:
            if self._is_unique_violation(e):
                already_exists = AlreadyExistsTopicCoveredException(
                    "Topic covered already exists for this profile and topic."
                )
                raise self._create_and_log_dependency_validation_exception(already_exists) from e
            raise self._create_and_log_dependency_exception(FailedTopicCoveredStorageException(str(e))) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedTopicCoveredStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    @staticmethod
    def _is_unique_violation(error: IntegrityError) -> bool:
        message = str(error.orig if error.orig is not None else error).lower()
        return any(marker in message for marker in _UNIQUE_VIOLATION_MARKERS)

    def _create_and_log_validation_exception(self, exception: Exception) -> TopicCoveredValidationException:
        validation_exception = TopicCoveredValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> TopicCoveredDependencyException:
        dependency_exception = TopicCoveredDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_dependency_validation_exception(
        self, exception: Exception
    ) -> TopicCoveredDependencyValidationException:
        dependency_validation_exception = TopicCoveredDependencyValidationException(inner_exception=exception)
        self._logging_broker.log_error(dependency_validation_exception)
        return dependency_validation_exception

    def _create_and_log_service_exception(self, exception: Exception) -> TopicCoveredServiceException:
        service_exception = TopicCoveredServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
