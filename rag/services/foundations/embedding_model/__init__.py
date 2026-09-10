from rag.services.foundations.embedding_model.i_embedding_model_service import (
    IEmbeddingModelService,
)
from rag.services.foundations.embedding_model.embedding_model_service_validations import (
    EmbeddingModelServiceValidations,
)
from rag.services.foundations.embedding_model.embedding_model_service_exceptions import (
    EmbeddingModelServiceExceptions,
)
from rag.services.foundations.embedding_model.embedding_model_service import (
    _EmbeddingModelServiceBase,
)


class EmbeddingModelService(
    _EmbeddingModelServiceBase,
    EmbeddingModelServiceValidations,
    EmbeddingModelServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    pattern, same as rag.services.ingestion.IngestionOrchestrationService one layer up.
    """


__all__ = [
    "IEmbeddingModelService",
    "EmbeddingModelService",
]
