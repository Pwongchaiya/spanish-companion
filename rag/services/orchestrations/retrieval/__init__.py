from rag.services.orchestrations.retrieval.i_retrieval_service import RetrievalService
from rag.services.orchestrations.retrieval.retrieval_service import (
    _HybridRetrievalServiceBase,
    LoggingBroker,
    StdlibLoggingBroker,
)
from rag.services.orchestrations.retrieval.retrieval_service_exceptions import HybridRetrievalServiceExceptions
from rag.services.orchestrations.retrieval.retrieval_service_validations import HybridRetrievalServiceValidations


class HybridRetrievalService(
    _HybridRetrievalServiceBase,
    HybridRetrievalServiceValidations,
    HybridRetrievalServiceExceptions,
):
    """Combines the base logic and exceptions mixins into the concrete
    Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs /
    EntitlementCodesOrchestrationService.Exeptions.cs /
    ...Validations.cs into one class.
    """


__all__ = [
    "RetrievalService",
    "HybridRetrievalService",
    "LoggingBroker",
    "StdlibLoggingBroker",
]
