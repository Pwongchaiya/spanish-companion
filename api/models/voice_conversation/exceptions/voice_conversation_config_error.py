"""Leaf exception raised by ConversationOrchestrator.run()."""

from api.errors import ApiError


class VoiceConversationConfigError(ApiError):
    """Raised when voice conversation fails due to missing or invalid configuration.

    Covers missing Azure Speech or Gemini API credentials, invalid audio device
    settings, or other startup configuration issues.
    """

    pass
