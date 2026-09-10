from api.services.orchestrations.voice_conversation.i_voice_conversation_service import VoiceConversationService
from api.services.orchestrations.voice_conversation.voice_conversation_service import (
    _ConversationOrchestrationServiceBase,
)
from api.services.orchestrations.voice_conversation.voice_conversation_service_exceptions import (
    ConversationOrchestrationServiceExceptions,
)


class ConversationOrchestrationService(
    _ConversationOrchestrationServiceBase,
    ConversationOrchestrationServiceExceptions,
):
    """Combines the base logic and exceptions mixins into the concrete
    Orchestration service -- mirrors ReviewOrchestrationService's
    _ReviewOrchestrationServiceBase + ReviewOrchestrationServiceExceptions merge exactly.

    No Validations mixin: nothing is validated at this tier (see
    voice_conversation_service.py's module docstring)."""


__all__ = [
    "VoiceConversationService",
    "ConversationOrchestrationService",
]
