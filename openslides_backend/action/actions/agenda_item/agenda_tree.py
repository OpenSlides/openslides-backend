from collections import defaultdict
from collections.abc import Iterable
from typing import Any

import roman

from ....models.models import AgendaItem


def to_roman(number: int) -> str:
    """
    Converts an arabic number within range from 1 to 4999 to the
    corresponding roman number. Returns the input converted as string on error
    conditions or higher numbers.
    """
    try:
        return roman.toRoman(number)
    except (roman.NotIntegerError, roman.OutOfRangeError):
        return str(number)


class TreeElement:
    def __init__(self, item_id: int, children: Iterable["TreeElement"]) -> None:
        self.id = item_id
        self.children = children


SerializedAgendaItem = dict[str, Any]


class AgendaTree:
    """
    Functionality to number the agenda tree.
    """

    DEFAULT_AGENDA_ITEM_TYPE = AgendaItem.AGENDA_ITEM

    def __init__(self, agenda_items: Iterable[SerializedAgendaItem]) -> None:
        self.ordered_agenda_items = sorted(
            agenda_items, key=lambda item: item.get("weight", 0)
        )

    def get_root_and_children(
        self, only_item_type: str | None = None
    ) -> tuple[Iterable[SerializedAgendaItem], dict[int, list[SerializedAgendaItem]]]:
        """
        Returns an iterable with all root items and a dictonary where the key is an
        item id and the value is a list with all children of the item.

        If only_item_type is given, the tree hides items with other types and
        all of their children.
        """
        item_children: dict[int, list[SerializedAgendaItem]] = defaultdict(list)
        root_items = []
        for item in self.ordered_agenda_items:
            item_type = item.get("type", self.DEFAULT_AGENDA_ITEM_TYPE)
            if only_item_type is not None and item_type != only_item_type:
                continue
            if item.get("parent_id") is not None:
                item_children[item["parent_id"]].append(item)
            else:
                root_items.append(item)
        return root_items, item_children

    def get_tree(self, only_item_type: str | None = None) -> Iterable[TreeElement]:
        """
        Generator that yields dictonaries. Each dictonary has two keys, id
        and children, where id is the id of one agenda item and children is a
        generator that yields dictonaries like the one discribed.

        If only_item_type is given, the tree hides items with other types and
        all of their children.
        """
        root_items, item_children = self.get_root_and_children(
            only_item_type=only_item_type
        )

        def get_children(
            items: Iterable[SerializedAgendaItem],
        ) -> Iterable[TreeElement]:
            """
            Generator that yields the descibed diconaries.
            """
            for item in items:
                yield TreeElement(
                    item_id=item["id"],
                    children=get_children(item_children[item["id"]]),
                )

        yield from get_children(root_items)

    def get_only_non_public_items(self) -> Iterable[SerializedAgendaItem]:
        """
        Generator, which yields only internal and hidden items, that means only items
        which type is INTERNAL_ITEM or HIDDEN_ITEM or which are children of non public items.
        """
        root_items, item_children = self.get_root_and_children(only_item_type=None)

        def yield_items(
            items: Iterable[SerializedAgendaItem], parent_is_not_public: bool = False
        ) -> Iterable[SerializedAgendaItem]:
            """
            Generator that yields a list of items and their children.
            """
            for item in items:
                item_type = item.get("type", self.DEFAULT_AGENDA_ITEM_TYPE)
                if parent_is_not_public or item_type in (
                    AgendaItem.INTERNAL_ITEM,
                    AgendaItem.HIDDEN_ITEM,
                ):
                    item_is_not_public = True
                    yield item
                else:
                    item_is_not_public = False
                yield from yield_items(
                    item_children.get(item["id"], []),
                    parent_is_not_public=item_is_not_public,
                )

        yield from yield_items(root_items)

    def number_all(
        self,
        numeral_system: str = "arabic",
        agenda_number_prefix: str | None = None,
    ) -> dict[int, str]:
        """
        Auto numbering of the agenda according to the numeral_system. Manually
        added item numbers will be overwritten.
        """
        new_numbers: dict[int, str] = {}

        # Start numbering visable agenda items.
        def walk_tree(tree: Iterable[TreeElement], number: str | None = None) -> None:
            for index, tree_element in enumerate(tree):
                # Calculate number of visable agenda items.
                if numeral_system == "roman" and number is None:
                    item_number = to_roman(index + 1)
                else:
                    item_number = str(index + 1)
                    if number is not None:
                        item_number = ".".join((number, item_number))
                # Add prefix.
                if agenda_number_prefix:
                    item_number_tmp = f"{agenda_number_prefix} {item_number}"
                else:
                    item_number_tmp = item_number
                # Save the new value and go down the tree.
                new_numbers[tree_element.id] = item_number_tmp
                walk_tree(tree_element.children, item_number)

        walk_tree(self.get_tree(only_item_type=AgendaItem.AGENDA_ITEM))

        # Reset number of hidden items.
        for item in self.get_only_non_public_items():
            new_numbers[item["id"]] = ""

        return new_numbers
