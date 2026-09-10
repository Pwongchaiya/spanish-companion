"""Leaf exception raised by ConversationOrchestrationService.run()."""

from api.errors import ApiError


class VoiceConversationPipelineError(ApiError):
    """Raised when the voice conversation pipeline fails at runtime.

    Covers audio device initialization failures, pipeline setup timeouts,
    unrecoverable LLM failures after retry, or other pipeline-level issues.
    """

    pass
