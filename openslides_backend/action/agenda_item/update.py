from typing import Any, Dict

from ...models.agenda_item import AgendaItem
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.schema import schema_version
from ..generics import UpdateAction

update_agenda_item_schema = {
    "$schema": schema_version,
    "title": "Update agenda item schema",
    "description": "An array of agenda items to be updated.",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            **AgendaItem().get_properties("id", "item_number", "comment"),
            "content_object_id": {
                "type": "string",
                "pattern": "^[a-z]([a-z_]*[a-z])?/[1-9][0-9]*$",
            },
        },
        "required": ["id"],
        "additionalProperties": False,
    },
    "minItems": 1,
    "uniqueItems": True,
}


class AgendaItemUpdate(UpdateAction):
    """
    Action to update agenda items.
    """

    model = AgendaItem()
    schema = update_agenda_item_schema

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        collection_name, id = instance["content_object_id"].split("/")
        instance["content_object_id"] = FullQualifiedId(
            Collection(collection_name), int(id)
        )
        return instance
