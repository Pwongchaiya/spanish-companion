"""Exposure-tier catch-all exception for TtsService."""

from api.errors import ApiError


class TtsServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised -- the
    final safety net so nothing escapes this service unwrapped.

    Mirrors FlagServiceException's shape
    (api/models/foundations/flag/exceptions/flag_service_exception.py).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Tts service error occurred. Contact support.", inner_exception)
