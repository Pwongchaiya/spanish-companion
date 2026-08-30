"""Catch/wrap/log safety net for GenerationService.

Mirrors EntitlementService.Exeptions.cs:85-93's final
`catch (Exception exception)` block -> CreateAndLogServiceException
(EntitlementService.Exeptions.cs:159-170) -- every reference Foundation
service ends its TryCatch with this "nothing escapes unwrapped" guarantee.
Generation currently has none: a bug inside explain() (e.g. an
AttributeError from a malformed flag/chunk object) propagates completely
raw today. This mixin is the one new tier this dispatch adds -- no
leaf/validation exceptions to catch, since there is nothing to validate
(see generation_service.py's docstring), so there is no
generation_service_validations.py counterpart the way Session Lifecycle
has one.

Deliberately does NOT catch GenerationError -- that is already caught and
swallowed to a fixed fallback string inside
_GenerationServiceBase._explain(), so it never reaches this mixin's
`except Exception` clause. The swallow-to-fallback try/except stays exactly
as it was before this rebuild.
"""

from typing import Callable

from rag.models.generation import Explanation
from rag.models.generation.exceptions import GenerationServiceException


class GenerationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], Explanation]) -> Explanation:
        try:
            return fn()
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_service_exception(self, exception: Exception) -> GenerationServiceException:
        """Mirrors CreateAndLogServiceException, EntitlementService.Exeptions.cs:159-170."""
        service_exception = GenerationServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
