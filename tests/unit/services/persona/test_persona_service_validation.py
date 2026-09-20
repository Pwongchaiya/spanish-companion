"""Input validation: every rejection happens before the broker is touched,
asserted explicitly on call_count."""

import pytest

from api.models.foundations.persona.exceptions import InvalidPersonaException, PersonaValidationException


def _assert_no_broker_calls(broker):
    for name in (
        "insert_persona",
        "select_persona_by_id",
        "select_persona_by_slug",
        "select_all_personas",
        "update_persona",
        "delete_persona",
    ):
        assert getattr(broker, name).call_count == 0, name


def _assert_rejected(call, broker, field):
    with pytest.raises(PersonaValidationException) as caught:
        call()

    assert isinstance(caught.value.inner_exception, InvalidPersonaException)
    assert field in caught.value.inner_exception.errors
    _assert_no_broker_calls(broker)


@pytest.mark.parametrize("method", ["create_persona", "update_persona"])
class TestWriteValidation:

    def _persona(self, method, make_persona, **overrides):
        return make_persona(**({"id": 1} | overrides))

    def test_should_reject_none_persona(self, service, mock_persona_broker, method):
        _assert_rejected(lambda: getattr(service, method)(None), mock_persona_broker, "persona")

    @pytest.mark.parametrize("field", ["slug", "name", "setting"])
    @pytest.mark.parametrize("bad", [None, "", "   ", 5])
    def test_should_reject_blank_text_field(self, service, mock_persona_broker, make_persona, method, field, bad):
        persona = self._persona(method, make_persona, **{field: bad})
        _assert_rejected(lambda: getattr(service, method)(persona), mock_persona_broker, field)

    @pytest.mark.parametrize("bad", [5, ["x"]])
    def test_should_reject_non_text_memory(self, service, mock_persona_broker, make_persona, method, bad):
        persona = self._persona(method, make_persona, memory=bad)
        _assert_rejected(lambda: getattr(service, method)(persona), mock_persona_broker, "memory")

    def test_should_reject_non_datetime_updated_at(self, service, mock_persona_broker, make_persona, method):
        persona = self._persona(method, make_persona, updated_at="2026-01-02")
        _assert_rejected(lambda: getattr(service, method)(persona), mock_persona_broker, "updated_at")

    def test_should_report_every_failing_field_at_once(self, service, mock_persona_broker, make_persona, method):
        persona = self._persona(method, make_persona, slug="", name=" ", setting=None)

        with pytest.raises(PersonaValidationException) as caught:
            getattr(service, method)(persona)

        assert set(caught.value.inner_exception.errors) == {"slug", "name", "setting"}
        _assert_no_broker_calls(mock_persona_broker)


class TestUpdateIdValidation:

    @pytest.mark.parametrize("bad_id", [None, 0, -1, True, "3"])
    def test_should_reject_invalid_id(self, service, mock_persona_broker, make_persona, bad_id):
        _assert_rejected(lambda: service.update_persona(make_persona(id=bad_id)), mock_persona_broker, "id")


class TestCreateIgnoresId:

    def test_should_not_require_id(self, service, mock_persona_broker, make_persona):
        submitted = make_persona(id=None)
        mock_persona_broker.insert_persona.return_value = submitted

        service.create_persona(submitted)

        assert mock_persona_broker.insert_persona.call_count == 1


class TestLookupValidation:

    @pytest.mark.parametrize("method", ["get_persona_by_id", "delete_persona"])
    @pytest.mark.parametrize("bad_id", [None, 0, -1, True, "3"])
    def test_should_reject_invalid_persona_id(self, service, mock_persona_broker, method, bad_id):
        _assert_rejected(lambda: getattr(service, method)(bad_id), mock_persona_broker, "persona_id")

    @pytest.mark.parametrize("bad_slug", [None, "", "  ", 5])
    def test_should_reject_blank_slug(self, service, mock_persona_broker, bad_slug):
        _assert_rejected(lambda: service.get_persona_by_slug(bad_slug), mock_persona_broker, "slug")
