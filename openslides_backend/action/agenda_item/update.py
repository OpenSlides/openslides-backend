from ...models.agenda_item import AgendaItem
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import UpdateAction


@register_action("agenda_item.update")
class AgendaItemUpdate(UpdateAction):
    """
    Action to update agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_update_schema(
        properties=[
            "item_number",
            "comment",
            "closed",
            "type",
            "weight",
            "tag_ids",
            "duration",
        ]
    )
