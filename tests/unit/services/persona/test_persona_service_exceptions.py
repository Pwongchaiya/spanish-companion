"""Exception dispatch: which raw failure maps to which wrapper tier, and that
every wrap is logged exactly once. A unique-slug IntegrityError is the
DependencyValidation tier; any other IntegrityError is a plain storage failure."""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from api.models.foundations.persona.exceptions import (
    AlreadyExistsPersonaException,
    FailedPersonaStorageException,
    PersonaDependencyException,
    PersonaDependencyValidationException,
    PersonaServiceException,
)


class TestDependencyTier:

    def test_should_wrap_operational_error_on_create(
        self, service, mock_persona_broker, mock_logging_broker, make_persona
    ):
        mock_persona_broker.insert_persona.side_effect = OperationalError("INSERT", {}, Exception("connection refused"))

        with pytest.raises(PersonaDependencyException) as caught:
            service.create_persona(make_persona())

        assert isinstance(caught.value.inner_exception, FailedPersonaStorageException)
        assert mock_persona_broker.insert_persona.call_count == 1
        assert mock_logging_broker.log_error.call_count == 1

    @pytest.mark.parametrize(
        "call, broker_method, args",
        [
            ("get_persona_by_id", "select_persona_by_id", (1,)),
            ("get_persona_by_slug", "select_persona_by_slug", ("cafe",)),
            ("list_personas", "select_all_personas", ()),
            ("delete_persona", "delete_persona", (1,)),
        ],
    )
    def test_should_wrap_operational_error_on_read_and_delete(
        self, service, mock_persona_broker, mock_logging_broker, call, broker_method, args
    ):
        getattr(mock_persona_broker, broker_method).side_effect = OperationalError(
            "SQL", {}, Exception("connection refused")
        )

        with pytest.raises(PersonaDependencyException):
            getattr(service, call)(*args)

        assert getattr(mock_persona_broker, broker_method).call_count == 1
        assert mock_logging_broker.log_error.call_count == 1

    def test_should_wrap_operational_error_on_update(
        self, service, mock_persona_broker, mock_logging_broker, make_persona
    ):
        mock_persona_broker.update_persona.side_effect = OperationalError("UPDATE", {}, Exception("connection refused"))

        with pytest.raises(PersonaDependencyException):
            service.update_persona(make_persona(id=1))

        assert mock_persona_broker.update_persona.call_count == 1
        assert mock_logging_broker.log_error.call_count == 1

    def test_should_wrap_non_unique_integrity_error_as_plain_dependency(
        self, service, mock_persona_broker, mock_logging_broker, make_persona
    ):
        mock_persona_broker.insert_persona.side_effect = IntegrityError("INSERT", {}, Exception("not-null violation"))

        with pytest.raises(PersonaDependencyException) as caught:
            service.create_persona(make_persona())

        assert isinstance(caught.value.inner_exception, FailedPersonaStorageException)
        assert mock_persona_broker.insert_persona.call_count == 1
        assert mock_logging_broker.log_error.call_count == 1


class TestDependencyValidationTier:

    @pytest.mark.parametrize("call", ["create_persona", "update_persona"])
    def test_should_wrap_unique_violation_as_already_exists(
        self, service, mock_persona_broker, mock_logging_broker, make_persona, call
    ):
        error = IntegrityError("SQL", {}, Exception("duplicate key value violates unique constraint uq_persona_slug"))
        mock_persona_broker.insert_persona.side_effect = error
        mock_persona_broker.update_persona.side_effect = error

        with pytest.raises(PersonaDependencyValidationException) as caught:
            getattr(service, call)(make_persona(id=1))

        assert isinstance(caught.value.inner_exception, AlreadyExistsPersonaException)
        assert mock_logging_broker.log_error.call_count == 1


class TestServiceTier:

    def test_should_wrap_unexpected_error_as_service_exception(self, service, mock_persona_broker, mock_logging_broker):
        mock_persona_broker.select_all_personas.side_effect = ValueError("boom")

        with pytest.raises(PersonaServiceException) as caught:
            service.list_personas()

        assert isinstance(caught.value.inner_exception, ValueError)
        assert mock_persona_broker.select_all_personas.call_count == 1
        assert mock_logging_broker.log_error.call_count == 1


class TestValidationTierLogging:

    def test_should_log_once_when_validation_fails(self, service, mock_persona_broker, mock_logging_broker):
        with pytest.raises(Exception):
            service.create_persona(None)

        assert mock_persona_broker.insert_persona.call_count == 0
        assert mock_logging_broker.log_error.call_count == 1
