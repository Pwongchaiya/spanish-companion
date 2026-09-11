"""Catch/wrap/log helpers for LearnerProfileService.

Mirrors UserProfileService.Exceptions.cs's dispatch shape (NL.Core.Users,
Services/Foundations/UserProfiles/UserProfileService.Exceptions.cs:22-86):
a specific-exception-type dispatch table, not a flat 3-bucket catch-all.
`_try_catch` returns fn()'s value since every public method here produces a
LearnerProfile.

No AlreadyExists/DependencyValidation tier here, unlike
MistakePatternServiceExceptions -- `learner_profile` has no unique
constraint beyond its primary key today, so there is no DB-detected
business-rule conflict for IntegrityError to classify (see
learner_profile_service.py's docstring for the full reasoning: a schema
change to enforce the singleton at the DB level is a schema decision, out
of scope for this rebuild per CLAUDE.md's "Ask Before Building" rule).
Every SQLAlchemyError (including IntegrityError) therefore falls to the
plain dependency-tier catch-all, mirroring MistakePatternServiceExceptions'
own generic SQLAlchemyError branch.
"""

from typing import Callable, TypeVar

from sqlalchemy.exc import SQLAlchemyError

from api.models.foundations.learner_profile.exceptions import (
    FailedLearnerProfileStorageException,
    InvalidLearnerProfileException,
    LearnerProfileDependencyException,
    LearnerProfileServiceException,
    LearnerProfileValidationException,
    NotFoundLearnerProfileException,
)

T = TypeVar("T")


class LearnerProfileServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except InvalidLearnerProfileException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotFoundLearnerProfileException as e:
            raise self._create_and_log_validation_exception(e) from e
        except SQLAlchemyError as e:
            raise self._create_and_log_dependency_exception(FailedLearnerProfileStorageException(str(e))) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> LearnerProfileValidationException:
        validation_exception = LearnerProfileValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_dependency_exception(self, exception: Exception) -> LearnerProfileDependencyException:
        dependency_exception = LearnerProfileDependencyException(inner_exception=exception)
        self._logging_broker.log_error(dependency_exception)
        return dependency_exception

    def _create_and_log_service_exception(self, exception: Exception) -> LearnerProfileServiceException:
        service_exception = LearnerProfileServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
