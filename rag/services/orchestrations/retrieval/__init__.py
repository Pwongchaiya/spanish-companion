from rag.brokers.logging import StdlibLoggingBroker
from rag.services.orchestrations.retrieval.i_retrieval_service import RetrievalService
from rag.services.orchestrations.retrieval.retrieval_service import LoggingBroker, _HybridRetrievalOrchestrationServiceBase
from rag.services.orchestrations.retrieval.retrieval_service_exceptions import HybridRetrievalOrchestrationServiceExceptions
from rag.services.orchestrations.retrieval.retrieval_service_validations import HybridRetrievalOrchestrationServiceValidations


class HybridRetrievalOrchestrationService(
    _HybridRetrievalOrchestrationServiceBase,
    HybridRetrievalOrchestrationServiceValidations,
    HybridRetrievalOrchestrationServiceExceptions,
):
    """Combines the base logic and exceptions mixins into the concrete
    Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs /
    EntitlementCodesOrchestrationService.Exeptions.cs /
    ...Validations.cs into one class.
    """


__all__ = [
    "RetrievalService",
    "HybridRetrievalOrchestrationService",
    "LoggingBroker",
    "StdlibLoggingBroker",
]
