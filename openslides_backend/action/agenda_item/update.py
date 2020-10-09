from ...models.models import AgendaItem
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("agenda_item.update")
class AgendaItemUpdate(UpdateAction):
    """
    Action to update agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_update_schema(
        optional_properties=[
            "item_number",
            "comment",
            "closed",
            "type",
            "weight",
            "tag_ids",
            "duration",
        ]
    )
