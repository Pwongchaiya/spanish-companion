"""Exposure-tier catch-all exception for GenerationService."""

from rag.errors import RagError


class GenerationServiceException(RagError):
    """Catch-all wrapper for any exception not otherwise recognised — the
    final safety net so nothing escapes this service unwrapped.

    Mirrors EntitlementService.Exeptions.cs:85-93's final
    `catch (Exception exception)` block, which every TryCatch method in the
    reference project ends with -- wraps into FailedEntitlementServiceException
    -> EntitlementServiceException. This project collapses that into one
    tier (no separate Failed*ServiceException), matching the precedent set
    by api/models/foundations/session_lifecycle/exceptions/session_service_exception.py's
    SessionServiceException -- Generation has no storage/dependency layer
    beneath it worth distinguishing either.

    `inner_exception` is carried by RagError itself (rag/errors.py), mirroring
    api/errors.py's ApiError.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Generation service error occurred. Contact support.", inner_exception)
