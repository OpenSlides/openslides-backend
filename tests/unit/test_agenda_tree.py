from typing import Any
from unittest import TestCase

from openslides_backend.action.agenda_item.agenda_tree import AgendaTree, to_roman
from openslides_backend.models.models import AgendaItem


class AgendaTreeTest(TestCase):
    def test_mixed_types(self) -> None:
        data = [
            {"id": 1, "type": AgendaItem.AGENDA_ITEM},
            {"id": 2, "type": AgendaItem.HIDDEN_ITEM},
        ]
        result = AgendaTree(data).number_all()
        assert result == {1: "1", 2: ""}

    def test_roman(self) -> None:
        data = [{"id": 1}]
        result = AgendaTree(data).number_all(numeral_system="roman")
        assert result == {1: "I"}

    def test_to_roman_exception(self) -> None:
        value: Any = "x"
        assert to_roman(value) == "x"

    def test_prefix(self) -> None:
        data = [{"id": 1}]
        result = AgendaTree(data).number_all(agenda_number_prefix="PRE")
        assert result == {1: "PRE 1"}
