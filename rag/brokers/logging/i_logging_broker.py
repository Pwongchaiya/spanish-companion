"""LoggingBroker — logging contract for every rag-layer Orchestration/
Foundation service's `_create_and_log_*` methods.

Local to `rag`, not imported from `api.brokers.logging`: `rag` must never
import from `api` (one-directional dependency: api -> rag). This is the
rag-side twin of `api/brokers/logging/i_logging_broker.py` — structurally
identical, so `api.brokers.logging.StdlibLoggingBroker` satisfies this
Protocol too and can be injected directly from `api/app.py`'s composition
root when a caller wants every service (api- and rag-side) to share one
logger instance.

Plays the role of `ILoggingBroker` on
EntitlementCodesOrchestrationService.cs:22 / EntitlementService.cs's
equivalent constructor parameter — every `_create_and_log_*` method logs
through it before raising.

Consolidated here after Ingestion, Retrieval, and Generation's rebuilds
each independently defined the identical Protocol + default impl locally
(the "one duplicate is cheaper than a package with one consumer" ponytail
note no longer applied once a second, then third, consumer showed up).
"""

from typing import Protocol


class LoggingBroker(Protocol):
    """Logging contract for rag-layer services."""

    def log_error(self, exception: Exception) -> None:
        """Log `exception` at ERROR level with its traceback."""
        ...
