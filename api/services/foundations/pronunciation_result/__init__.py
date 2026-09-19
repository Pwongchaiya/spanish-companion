"""Re-exports the concrete PronunciationResultService class, declared directly
in pronunciation_result_service.py (which inherits the Validations/Exceptions
mixins by name)."""

from api.services.foundations.pronunciation_result.i_pronunciation_result_service import IPronunciationResultService
from api.services.foundations.pronunciation_result.pronunciation_result_service import PronunciationResultService

__all__ = [
    "IPronunciationResultService",
    "PronunciationResultService",
]
