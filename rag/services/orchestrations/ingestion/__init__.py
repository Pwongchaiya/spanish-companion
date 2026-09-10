from rag.services.orchestrations.ingestion.i_ingestion_service import IIngestionService
from rag.services.orchestrations.ingestion.ingestion_service import (
    _IngestionOrchestrationServiceBase,
    chunk_text,
    CHUNKING_STRATEGY_VERSION,
    LoggingBroker,
)
from rag.services.orchestrations.ingestion.ingestion_service_validations import IngestionOrchestrationServiceValidations
from rag.services.orchestrations.ingestion.ingestion_service_exceptions import IngestionOrchestrationServiceExceptions


class IngestionOrchestrationService(
    _IngestionOrchestrationServiceBase,
    IngestionOrchestrationServiceValidations,
    IngestionOrchestrationServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs / .Validations.cs / .Exeptions.cs
    into one class.
    """


__all__ = [
    "IIngestionService",
    "IngestionOrchestrationService",
    "LoggingBroker",
    "chunk_text",
    "CHUNKING_STRATEGY_VERSION",
]
