from typing import Any, Dict

from ...models.agenda_item import AgendaItem
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.schema import schema_version
from ..action import register_action
from ..generics import CreateAction

create_agenda_item_schema = {
    "$schema": schema_version,
    "title": "New agenda items schema",
    "description": "An array of new agenda items.",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            **AgendaItem().get_properties("meeting_id", "item_number", "comment"),
            "content_object_id": {
                "type": "string",
                "pattern": "^[a-z]([a-z_]*[a-z])?/[1-9][0-9]*$",
            },
        },
        "required": ["meeting_id"],
        "additionalProperties": False,
    },
    "minItems": 1,
    "uniqueItems": False,
}


@register_action("agenda_item.create")
class AgendaItemCreate(CreateAction):
    """
    Action to create agenda items.
    """

    model = AgendaItem()
    schema = create_agenda_item_schema

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        collection_name, id = instance["content_object_id"].split("/")
        instance["content_object_id"] = FullQualifiedId(
            Collection(collection_name), int(id)
        )
        return instance
