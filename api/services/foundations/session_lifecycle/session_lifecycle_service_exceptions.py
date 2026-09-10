"""Catch/wrap/log helpers for ConversationSessionService.

Mirrors EntitlementService.Exeptions.cs:22-94's TryCatch: catch each known
leaf exception, wrap + log it, re-raise the wrapper. Anything else falls
through the final `except Exception` safety net (mirrors
EntitlementService.Exeptions.cs:85-93), matching the reference project's
"nothing escapes this service unwrapped" guarantee.
"""

import subprocess
from typing import Callable

from api.models.foundations.session_lifecycle.exceptions import (
    AlreadyRunningSessionException,
    NotRunningSessionException,
    SessionServiceException,
    SessionValidationException,
)


class ConversationSessionServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging."""

    def _try_catch(self, fn: Callable[[], None]) -> None:
        try:
            fn()
        except subprocess.TimeoutExpired:
            # ponytail: OS-level anomaly (SIGKILL/TerminateProcess sent by
            # _stop()'s escalation but never reaped) outside this feature's
            # two-exception vocabulary -- deliberately let it propagate raw,
            # unwrapped, rather than folding it into the generic Exception
            # catch-all below. This is the ONE explicit, cited divergence
            # from NL.Core.Entitlements' pattern in this whole rebuild: its
            # final `catch (Exception exception)`
            # (EntitlementService.Exeptions.cs:85-93) wraps literally
            # everything with no carve-out. Preserved here on purpose --
            # it's the existing, already-tested regression contract
            # (test_should_propagate_timeout_expired_when_kill_is_not_
            # honoured in
            # tests/unit/services/session_lifecycle/test_stop_logic.py) and
            # changing it was explicitly rejected when raised during this
            # rebuild -- fix code to preserve the test, never weaken the
            # test to fit the code.
            raise
        except AlreadyRunningSessionException as e:
            raise self._create_and_log_validation_exception(e) from e
        except NotRunningSessionException as e:
            raise self._create_and_log_validation_exception(e) from e
        except Exception as e:
            raise self._create_and_log_service_exception(e) from e

    def _create_and_log_validation_exception(self, exception: Exception) -> SessionValidationException:
        """Mirrors CreateAndLogValidationException, EntitlementService.Exeptions.cs:122-133."""
        validation_exception = SessionValidationException(inner_exception=exception)
        self._logging_broker.log_error(validation_exception)
        return validation_exception

    def _create_and_log_service_exception(self, exception: Exception) -> SessionServiceException:
        """Mirrors CreateAndLogServiceException, EntitlementService.Exeptions.cs:159-170."""
        service_exception = SessionServiceException(inner_exception=exception)
        self._logging_broker.log_error(service_exception)
        return service_exception
