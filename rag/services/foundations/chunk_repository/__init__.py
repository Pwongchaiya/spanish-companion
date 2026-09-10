from rag.services.foundations.chunk_repository.i_chunk_repository_service import IChunkRepositoryService
from rag.services.foundations.chunk_repository.chunk_repository_service import _ChunkRepositoryServiceBase
from rag.services.foundations.chunk_repository.chunk_repository_service_validations import (
    ChunkRepositoryServiceValidations,
)
from rag.services.foundations.chunk_repository.chunk_repository_service_exceptions import (
    ChunkRepositoryServiceExceptions,
)


class ChunkRepositoryService(
    _ChunkRepositoryServiceBase,
    ChunkRepositoryServiceValidations,
    ChunkRepositoryServiceExceptions,
):
    """Combines the base logic, validations, and exceptions mixins into the
    concrete Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Validations.cs / .Exeptions.cs into one class,
    the same pattern IngestionOrchestrationService uses one layer up.
    """


__all__ = [
    "IChunkRepositoryService",
    "ChunkRepositoryService",
]
