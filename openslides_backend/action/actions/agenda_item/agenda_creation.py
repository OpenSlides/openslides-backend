from typing import Any

from ....models.models import AgendaItem
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import id_list_schema, optional_id_schema
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
        "description": "The weight of the agenda item.",
        "type": "integer",
    },
    f"{AGENDA_PREFIX}tag_ids": {
        "description": "The ids of tags to be set.",
        **id_list_schema,
    },
}


class CreateActionWithAgendaItemMixin(Action):
    """
    Mixin that can be used to create an agenda item as a dependency.
    Just call the functions in the corresponding base functions.
    """

    def check_dependant_action_execution_agenda_item(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> bool:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["agenda_item_creation"],
            lock_result=False,
        )
        agenda_item_creation = meeting.get("agenda_item_creation")
        agenda_create = instance.pop("agenda_create", None)
        result_value: bool
        if agenda_item_creation == "always":
            return True
        elif agenda_item_creation == "never":
            result_value = False
        elif agenda_create is not None:
            result_value = agenda_create
        elif agenda_item_creation == "default_yes":
            result_value = True
        else:
            result_value = False

        if not result_value:
            for extra_field in agenda_creation_properties.keys():
                instance.pop(extra_field, None)

        return result_value

    def get_dependent_action_data_agenda_item(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> list[dict[str, Any]]:
        agenda_item_action_data = self.remove_agenda_prefix_from_fieldnames(instance)
        agenda_item_action_data["content_object_id"] = fqid_from_collection_and_id(
            self.model.collection, instance["id"]
        )
        return [agenda_item_action_data]

    @staticmethod
    def remove_agenda_prefix_from_fieldnames(
        instance: dict[str, Any]
    ) -> dict[str, Any]:
        prefix_len = len(AGENDA_PREFIX)
        extra_field = f"{AGENDA_PREFIX}create"  # This field should not be provided to the AgendaItemCreate action.
        agenda_item = {
            field[prefix_len:]: value
            for field in agenda_creation_properties.keys()
            if field != extra_field and (value := instance.pop(field, None)) is not None
        }
        return agenda_item
