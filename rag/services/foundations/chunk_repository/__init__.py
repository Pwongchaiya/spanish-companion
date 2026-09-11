"""Re-exports the concrete ChunkRepositoryService class, declared directly in
chunk_repository_service.py (which inherits the Validations/Exceptions
mixins by name) -- no composition step here, matching LearnerProfileService's
rebuilt one-class-declared-once shape.
"""

from rag.services.foundations.chunk_repository.chunk_repository_service import ChunkRepositoryService
from rag.services.foundations.chunk_repository.i_chunk_repository_service import IChunkRepositoryService

__all__ = [
    "IChunkRepositoryService",
    "ChunkRepositoryService",
]
