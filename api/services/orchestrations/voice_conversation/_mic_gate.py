"""Pipecat frame filter: echo suppression for ConversationOrchestrationService's
pipeline. Split out of voice_conversation_service.py so the orchestration
file holds only the orchestrator itself, matching Review's one-class(-ish)
per file precedent (review_service.py / review_service_exceptions.py).
"""

from pipecat.frames.frames import BotStartedSpeakingFrame, BotStoppedSpeakingFrame, InputAudioRawFrame


class _MicGate:
    """Drops mic audio while the bot is speaking.

    LocalAudioTransport has no acoustic echo cancellation, so without this the
    mic hears the bot's own TTS output through the speakers and streams it to
    Azure STT. AlwaysUserMuteStrategy alone doesn't stop that: it filters
    downstream of STT, but Azure's cloud endpointing finalizes a "recognized"
    transcript of the echo the instant TTS audio stops, landing right as that
    mute window closes. Gating here, before STT ever sees the audio, removes
    the echo transcript instead of racing to drop it after the fact.

    Only gates InputAudioRawFrame — everything else passes through untouched.
    Needs filter_system_frames=True on the FunctionFilter wrapping this:
    InputAudioRawFrame is a SystemFrame, and FunctionFilter auto-passes those
    through by default, which otherwise makes this a no-op.
    """

    def __init__(self):
        self._bot_speaking = False

    async def __call__(self, frame) -> bool:
        if isinstance(frame, BotStartedSpeakingFrame):
            self._bot_speaking = True
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._bot_speaking = False
        if isinstance(frame, InputAudioRawFrame):
            return not self._bot_speaking
        return True
