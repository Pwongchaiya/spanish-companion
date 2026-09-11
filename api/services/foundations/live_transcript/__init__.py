"""Re-exports the concrete LiveTranscriptService class, declared directly in
live_transcript_service.py (which inherits the Exceptions mixin by name) --
no composition step here, matching LearnerProfileService's rebuilt
one-class-declared-once shape.
"""

from api.services.foundations.live_transcript.i_live_transcript_service import ILiveTranscriptService
from api.services.foundations.live_transcript.live_transcript_service import LiveTranscriptService

__all__ = [
    "ILiveTranscriptService",
    "LiveTranscriptService",
]
