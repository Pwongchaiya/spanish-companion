from rag.services.retrieval.i_retrieval_service import RetrievalService
from rag.services.retrieval.retrieval_service import (
    _HybridRetrievalServiceBase,
    LoggingBroker,
    StdlibLoggingBroker,
)
from rag.services.retrieval.retrieval_service_exceptions import HybridRetrievalServiceExceptions


class HybridRetrievalService(
    _HybridRetrievalServiceBase,
    HybridRetrievalServiceExceptions,
):
    """Combines the base logic and exceptions mixins into the concrete
    Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs /
    EntitlementCodesOrchestrationService.Exeptions.cs into one class.

    No Validations mixin: see retrieval_service_exceptions.py's module
    docstring for why Retrieval has no Validation tier.
    """


__all__ = [
    "RetrievalService",
    "HybridRetrievalService",
    "LoggingBroker",
    "StdlibLoggingBroker",
]
