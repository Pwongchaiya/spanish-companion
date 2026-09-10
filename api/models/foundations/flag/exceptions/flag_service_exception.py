"""Exposure-tier catch-all exception for FlagService."""

from api.errors import ApiError


class FlagServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised -- the
    final safety net so nothing escapes this service unwrapped.

    Mirrors IngestionOrchestrationServiceException's shape
    (rag/models/orchestrations/ingestion/exceptions/ingestion_orchestration_service_exception.py)
    -- the Failed* tier is collapsed away, same as the Session Lifecycle
    precedent: this service sits directly on a broker, so anything reaching
    the final catch is already raw, and a Failed* tier would only wrap a
    raw exception in a second name that carries no extra information.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Flag service error occurred. Contact support.", inner_exception)
