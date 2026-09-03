"""Foundation service for STT construction.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. No Validations/Exceptions
mixin split: a pure pass-through has neither to split out.
"""

from api.brokers.stt import SttBroker
from pipecat.services.azure.stt import AzureSTTService


class SttService:
    """Owns access to a configured bilingual Azure STT service."""

    def __init__(self, stt_broker: SttBroker) -> None:
        self._stt_broker = stt_broker

    def create(self) -> AzureSTTService:
        return self._stt_broker.create()
