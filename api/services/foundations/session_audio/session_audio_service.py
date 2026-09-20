"""Foundation service for the session_audio entity.

Wraps ISessionAudioBroker (api/brokers/session_audio/) with input validation
only. Single broker dependency -> Foundation layer. Logic + Validations +
Exceptions mixins, the concrete class declared here, mirroring
api/services/foundations/persona/persona_service.py.
"""

from datetime import datetime

from api.brokers.logging import LoggingBroker
from api.brokers.session_audio.i_session_audio_broker import ISessionAudioBroker
from api.models.foundations.session_audio.exceptions import NotFoundSessionAudioException
from api.models.foundations.session_audio.session_audio import SessionAudio
from api.services.foundations.session_audio.i_session_audio_service import ISessionAudioService
from api.services.foundations.session_audio.session_audio_service_exceptions import (
    SessionAudioServiceExceptions,
)
from api.services.foundations.session_audio.session_audio_service_validations import (
    SessionAudioServiceValidations,
)


class SessionAudioService(
    SessionAudioServiceExceptions,
    SessionAudioServiceValidations,
    ISessionAudioService,
):
    """Owns session_audio CRUD."""

    def __init__(
        self,
        session_audio_broker: ISessionAudioBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._session_audio_broker = session_audio_broker
        self._logging_broker = logging_broker

    def create_session_audio(self, session_audio: SessionAudio) -> SessionAudio:
        def action() -> SessionAudio:
            self._validate_session_audio_on_create(session_audio)
            return self._session_audio_broker.insert_session_audio(session_audio)

        return self._try_catch(action)

    def get_session_audio_by_session_log_id(self, session_log_id: int) -> SessionAudio:
        def action() -> SessionAudio:
            self._validate_id("session_log_id", session_log_id)
            maybe_row = self._session_audio_broker.select_session_audio_by_session_log_id(session_log_id)
            if maybe_row is None:
                raise NotFoundSessionAudioException()
            return maybe_row

        return self._try_catch(action)

    def list_session_audio_older_than(self, cutoff: datetime) -> list[SessionAudio]:
        def action() -> list[SessionAudio]:
            self._validate_cutoff(cutoff)
            return self._session_audio_broker.select_session_audio_older_than(cutoff)

        return self._try_catch(action)

    def delete_session_audio(self, session_audio_id: int) -> SessionAudio:
        def action() -> SessionAudio:
            self._validate_id("session_audio_id", session_audio_id)
            maybe_row = self._session_audio_broker.delete_session_audio(session_audio_id)
            if maybe_row is None:
                raise NotFoundSessionAudioException()
            return maybe_row

        return self._try_catch(action)
