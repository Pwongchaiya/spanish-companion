"""Catch/wrap/log helpers for ConversationOrchestrationService.

Mirrors ConversationSessionServiceExceptions/ReviewOrchestrationServiceExceptions's
shape: catch each known leaf, wrap + log it, re-raise the wrapper. One
structural difference from both of those, stated plainly rather than
glossed over: there is no distinct wrapper-tier exception class behind
_try_catch here. The two leaves it catches (KeyError, OSError) are raw
stdlib exceptions, not this feature's own; the two classes it wraps them
into (VoiceConversationConfigError, VoiceConversationPipelineError) are
still flat leaves inheriting ApiError directly -- the same two exceptions
this feature has always had, unchanged. What this file adopts is the
mechanical pattern (a dedicated _try_catch delegate + _create_and_log_*
helpers + an injected LoggingBroker), not a new leaf/wrapper hierarchy.

The leaves it catches are KeyError and OSError plus, since W3 of the
architecture conformance audit, the two wrapper-tier exceptions
LiveTranscriptService now raises in place of a raw OSError.

_try_catch only wraps ConversationOrchestrationService._setup() -- the live
conversation loop (runner.run()) and its finally-block cleanup are
deliberately not routed through this, same scope the old inline
try/except covered before this file existed.
"""

from typing import Awaitable, Callable, TypeVar

from api.models.foundations.live_transcript.exceptions import (
    LiveTranscriptDependencyException,
    LiveTranscriptServiceException,
)
from api.models.orchestrations.voice_conversation.exceptions import (
    VoiceConversationConfigError,
    VoiceConversationPipelineError,
)

T = TypeVar("T")


class ConversationOrchestrationServiceExceptions:
    """Mixin: centralised try/catch + exception creation/logging for
    ConversationOrchestrationService._setup()."""

    async def _try_catch(self, fn: Callable[[], Awaitable[T]]) -> T:
        try:
            return await fn()
        except KeyError as e:
            raise self._create_and_log_config_exception(e) from e
        except OSError as e:
            raise self._create_and_log_pipeline_exception(e) from e
        except (LiveTranscriptDependencyException, LiveTranscriptServiceException) as e:
            # W3: LiveTranscriptService now wraps its broker's OSErrors, so
            # they no longer arrive here as OSError. Mapped onto the same
            # VoiceConversationPipelineError as before, keeping this feature's
            # deliberately-resolved 2-exception external vocabulary (CLAUDE.md).
            raise self._create_and_log_pipeline_exception(e) from e

    def _create_and_log_config_exception(self, exception: Exception) -> VoiceConversationConfigError:
        config_exception = VoiceConversationConfigError(f"Missing required configuration: {exception}")
        self._logging_broker.log_error(config_exception)
        return config_exception

    def _create_and_log_pipeline_exception(self, exception: Exception) -> VoiceConversationPipelineError:
        pipeline_exception = VoiceConversationPipelineError(f"Audio device initialization failed: {exception}")
        self._logging_broker.log_error(pipeline_exception)
        return pipeline_exception
