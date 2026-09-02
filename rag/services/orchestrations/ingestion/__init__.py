from rag.services.orchestrations.ingestion.i_ingestion_service import IIngestionService
from rag.services.orchestrations.ingestion.ingestion_service import (
    _IngestionServiceBase,
    chunk_text,
    CHUNK_SIZE,
    CHUNKING_STRATEGY_VERSION,
    LoggingBroker,
)
from rag.services.orchestrations.ingestion.ingestion_service_validations import IngestionServiceValidations
from rag.services.orchestrations.ingestion.ingestion_service_exceptions import IngestionServiceExceptions


class IngestionService(
    _IngestionServiceBase,
    IngestionServiceValidations,
    IngestionServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Orchestration service -- mirrors C#'s `partial class` merging
    EntitlementCodesOrchestrationService.cs / .Validations.cs / .Exeptions.cs
    into one class.
    """


__all__ = [
    "IIngestionService",
    "IngestionService",
    "LoggingBroker",
    "chunk_text",
    "CHUNK_SIZE",
    "CHUNKING_STRATEGY_VERSION",
]
