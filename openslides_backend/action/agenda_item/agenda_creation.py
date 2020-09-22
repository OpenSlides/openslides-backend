from typing import Any, Dict, Type

from ...models.agenda_item import AgendaItem
from ...models.base import Model
from ...shared.patterns import KEYSEPARATOR
from ..base import Action
from ..create_action_with_dependencies import CreateActionWithDependencies
from .create import AgendaItemCreate

AGENDA_PREFIX = "agenda_"

agenda_creation_properties = {
    f"{AGENDA_PREFIX}create": {
        "description": "This flag controls whether an agenda item is created.",
        "type": "boolean",
    },
    f"{AGENDA_PREFIX}type": {
        "description": "The type of the agenda item (common, internal, hidden).",
        "type": "integer",
        "enum": [
            AgendaItem.AGENDA_ITEM,
            AgendaItem.INTERNAL_ITEM,
            AgendaItem.HIDDEN_ITEM,
        ],
    },
    f"{AGENDA_PREFIX}parent_id": {
        "description": "The id of the parent agenda item.",
        "type": ["integer", "null"],
        "minimum": 1,
    },
    f"{AGENDA_PREFIX}comment": {
        "description": "The comment of the agenda item.",
        "type": "string",
    },
    f"{AGENDA_PREFIX}duration": {
        "description": "The duration of this agenda item object in seconds.",
        "type": "integer",
        "minimum": 0,
    },
    f"{AGENDA_PREFIX}weight": {
        "description": "The weight of the agenda item. Submitting null defaults to 0.",
        "type": "integer",
    },
}


class CreateActionWithAgendaItemMixin:
    """
    Mixin that can be used to create an agenda item as a dependency.
    Just call the functions in the corresponding base functions.
    """

    model: Model

    def check_dependant_action_execution_agenda_item(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        # TODO
        return True

    def get_dependent_action_payload_agenda_item(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> Dict[str, Any]:
        agenda_item_payload_element = {
            "content_object_id": f"{str(self.model.collection)}{KEYSEPARATOR}{element['new_id']}",
        }
        for extra_field in agenda_creation_properties.keys():
            if extra_field == f"{AGENDA_PREFIX}create":
                # This field should not be provided to the AgendaItemCreate action.
                continue
            prefix_len = len(AGENDA_PREFIX)
            extra_field_without_prefix = extra_field[prefix_len:]
            value = element["instance"].pop(extra_field, None)
            if value is not None:
                agenda_item_payload_element[extra_field_without_prefix] = value
        return agenda_item_payload_element


class CreateActionWithAgendaItem(
    CreateActionWithDependencies, CreateActionWithAgendaItemMixin
):
    """
    Base action for dependent agenda item creation.
    """

    dependencies = [AgendaItemCreate]

    def check_dependant_action_execution(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        return self.check_dependant_action_execution_agenda_item(
            element, CreateActionClass
        )

    def get_dependent_action_payload(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> Dict[str, Any]:
        return self.get_dependent_action_payload_agenda_item(element, CreateActionClass)
