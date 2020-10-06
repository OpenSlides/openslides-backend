from ...models.models import AgendaItem
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("agenda_item.delete")
class AgendaItemDelete(DeleteAction):
    """
    Action to delete agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_delete_schema()
