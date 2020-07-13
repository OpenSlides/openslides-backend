import fastjsonschema  # type: ignore

from ...models.agenda_item import AgendaItem
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import DeleteAction

delete_agenda_item_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Delete agenda items schema",
        "description": "An array of agenda items to be deleted.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": AgendaItem().get_properties("id"),
            "required": ["id"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("agenda_item.delete")
class AgendaItemDelete(DeleteAction):
    """
    Action to delete agenda items.
    """

    model = AgendaItem()
    schema = delete_agenda_item_schema
