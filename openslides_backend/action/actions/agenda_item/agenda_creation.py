from typing import Any, Dict, Type

from ....models.models import AgendaItem
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ....shared.schema import optional_id_schema
from ...action import Action

AGENDA_PREFIX = "agenda_"

agenda_creation_properties = {
    f"{AGENDA_PREFIX}create": {
        "description": "This flag controls whether an agenda item is created.",
        "type": "boolean",
    },
    f"{AGENDA_PREFIX}type": {
        "description": "The type of the agenda item (common, internal, hidden).",
        "type": "string",
        "enum": [
            AgendaItem.AGENDA_ITEM,
            AgendaItem.INTERNAL_ITEM,
            AgendaItem.HIDDEN_ITEM,
        ],
    },
    f"{AGENDA_PREFIX}parent_id": {
        "description": "The id of the parent agenda item.",
        **optional_id_schema,
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


class CreateActionWithAgendaItemMixin(Action):
    """
    Mixin that can be used to create an agenda item as a dependency.
    Just call the functions in the corresponding base functions.
    """

    def check_dependant_action_execution_agenda_item(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            ["agenda_item_creation"],
            lock_result=True,
        )
        agenda_item_creation = meeting.get("agenda_item_creation")
        agenda_create = instance.get("agenda_create")
        if agenda_item_creation == "always":
            return True
        elif agenda_item_creation == "never":
            return False
        elif agenda_item_creation == "default_yes":
            result_default = True
        else:
            result_default = False

        if agenda_create is None:
            return result_default
        return agenda_create

    def get_dependent_action_payload_agenda_item(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action], index: int
    ) -> Dict[str, Any]:
        agenda_item_payload_element = {
            "content_object_id": f"{str(self.model.collection)}{KEYSEPARATOR}{instance['id']}",
        }
        for extra_field in agenda_creation_properties.keys():
            if extra_field == f"{AGENDA_PREFIX}create":
                # This field should not be provided to the AgendaItemCreate action.
                continue
            prefix_len = len(AGENDA_PREFIX)
            extra_field_without_prefix = extra_field[prefix_len:]
            value = instance.pop(extra_field, None)
            if value is not None:
                agenda_item_payload_element[extra_field_without_prefix] = value
        return agenda_item_payload_element
