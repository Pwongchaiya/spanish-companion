from api.services.foundations.live_transcript.i_live_transcript_service import ILiveTranscriptService
from api.services.foundations.live_transcript.live_transcript_service import _LiveTranscriptServiceBase
from api.services.foundations.live_transcript.live_transcript_service_exceptions import (
    LiveTranscriptServiceExceptions,
)


class LiveTranscriptService(_LiveTranscriptServiceBase, LiveTranscriptServiceExceptions):
    """Combines the base logic and exceptions mixins into the concrete
    Foundation service -- mirrors FlagService's multi-inheritance merge,
    which stands in for C#'s `partial class`.
    """


__all__ = [
    "ILiveTranscriptService",
    "LiveTranscriptService",
]
