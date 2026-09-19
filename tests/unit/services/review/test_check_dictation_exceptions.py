"""check_dictation is a pure function: it raises only ValueError, never wraps or swallows.

Wrapping into the Review exception tiers is the orchestrator's job -- see
test_dictation_orchestration.py.
"""

import pytest

from api.services.orchestrations.review._dictation import check_dictation


class TestCheckDictationExceptions:

    def test_should_raise_value_error_not_a_wrapper(self):
        with pytest.raises(ValueError) as caught:
            check_dictation("", "yo tengo")
        assert type(caught.value) is ValueError
