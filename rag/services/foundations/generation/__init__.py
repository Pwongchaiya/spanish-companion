from rag.services.foundations.generation.i_generation_service import FlagLike, IGenerationService
from rag.services.foundations.generation.generation_service import _GenerationServiceBase
from rag.services.foundations.generation.generation_service_exceptions import (
    GenerationServiceExceptions,
)


class GenerationService(_GenerationServiceBase, GenerationServiceExceptions):
    """Combines the base logic and exceptions mixins into the concrete
    Foundation service -- mirrors C#'s `partial class` merging
    EntitlementService.cs / .Exeptions.cs into one class. No
    .Validations.cs counterpart (see generation_service.py's docstring for
    why)."""


__all__ = [
    "FlagLike",
    "IGenerationService",
    "GenerationService",
]
