"""Happy-path flow: each public method delegates to exactly one broker call
and returns its result unchanged. Strict call-count verification."""

import pytest

from api.models.foundations.persona.exceptions import NotFoundPersonaException, PersonaValidationException


def _assert_only(broker, called: str, count: int = 1):
    for name in (
        "insert_persona",
        "select_persona_by_id",
        "select_persona_by_slug",
        "select_all_personas",
        "update_persona",
        "delete_persona",
    ):
        assert getattr(broker, name).call_count == (count if name == called else 0), name


class TestCreatePersona:

    def test_should_insert_and_return_broker_row(self, service, mock_persona_broker, make_persona):
        submitted = make_persona()
        stored = make_persona(id=7)
        mock_persona_broker.insert_persona.return_value = stored

        actual = service.create_persona(submitted)

        assert actual is stored
        mock_persona_broker.insert_persona.assert_called_once_with(submitted)
        _assert_only(mock_persona_broker, "insert_persona")

    def test_should_accept_memory_text(self, service, mock_persona_broker, make_persona):
        submitted = make_persona(memory="likes tea")
        mock_persona_broker.insert_persona.return_value = submitted

        service.create_persona(submitted)

        mock_persona_broker.insert_persona.assert_called_once_with(submitted)


class TestGetPersona:

    def test_should_return_row_by_id(self, service, mock_persona_broker, make_persona):
        row = make_persona(id=3)
        mock_persona_broker.select_persona_by_id.return_value = row

        assert service.get_persona_by_id(3) is row
        mock_persona_broker.select_persona_by_id.assert_called_once_with(3)
        _assert_only(mock_persona_broker, "select_persona_by_id")

    def test_should_return_row_by_slug(self, service, mock_persona_broker, make_persona):
        row = make_persona(id=3)
        mock_persona_broker.select_persona_by_slug.return_value = row

        assert service.get_persona_by_slug("cafe") is row
        mock_persona_broker.select_persona_by_slug.assert_called_once_with("cafe")
        _assert_only(mock_persona_broker, "select_persona_by_slug")

    def test_should_raise_not_found_when_id_missing(self, service, mock_persona_broker, mock_logging_broker):
        mock_persona_broker.select_persona_by_id.return_value = None

        with pytest.raises(PersonaValidationException) as caught:
            service.get_persona_by_id(3)

        assert isinstance(caught.value.inner_exception, NotFoundPersonaException)
        _assert_only(mock_persona_broker, "select_persona_by_id")
        assert mock_logging_broker.log_error.call_count == 1

    def test_should_raise_not_found_when_slug_missing(self, service, mock_persona_broker, mock_logging_broker):
        mock_persona_broker.select_persona_by_slug.return_value = None

        with pytest.raises(PersonaValidationException) as caught:
            service.get_persona_by_slug("nope")

        assert isinstance(caught.value.inner_exception, NotFoundPersonaException)
        _assert_only(mock_persona_broker, "select_persona_by_slug")
        assert mock_logging_broker.log_error.call_count == 1


class TestListPersonas:

    def test_should_return_broker_rows_unchanged(self, service, mock_persona_broker, make_persona):
        rows = [make_persona(id=1), make_persona(id=2, slug="market")]
        mock_persona_broker.select_all_personas.return_value = rows

        assert service.list_personas() == rows
        mock_persona_broker.select_all_personas.assert_called_once_with()
        _assert_only(mock_persona_broker, "select_all_personas")

    def test_should_return_empty_list_when_nothing_stored(self, service, mock_persona_broker):
        mock_persona_broker.select_all_personas.return_value = []

        assert service.list_personas() == []
        _assert_only(mock_persona_broker, "select_all_personas")


class TestUpdatePersona:

    def test_should_update_and_return_broker_row(self, service, mock_persona_broker, make_persona):
        submitted = make_persona(id=4, memory="met twice")
        mock_persona_broker.update_persona.return_value = submitted

        assert service.update_persona(submitted) is submitted
        mock_persona_broker.update_persona.assert_called_once_with(submitted)
        _assert_only(mock_persona_broker, "update_persona")

    def test_should_raise_not_found_when_id_missing(self, service, mock_persona_broker, make_persona):
        mock_persona_broker.update_persona.return_value = None

        with pytest.raises(PersonaValidationException) as caught:
            service.update_persona(make_persona(id=4))

        assert isinstance(caught.value.inner_exception, NotFoundPersonaException)
        _assert_only(mock_persona_broker, "update_persona")


class TestDeletePersona:

    def test_should_delete_and_return_row(self, service, mock_persona_broker, make_persona):
        row = make_persona(id=5)
        mock_persona_broker.delete_persona.return_value = row

        assert service.delete_persona(5) is row
        mock_persona_broker.delete_persona.assert_called_once_with(5)
        _assert_only(mock_persona_broker, "delete_persona")

    def test_should_raise_not_found_when_id_missing(self, service, mock_persona_broker):
        mock_persona_broker.delete_persona.return_value = None

        with pytest.raises(PersonaValidationException) as caught:
            service.delete_persona(5)

        assert isinstance(caught.value.inner_exception, NotFoundPersonaException)
        _assert_only(mock_persona_broker, "delete_persona")
