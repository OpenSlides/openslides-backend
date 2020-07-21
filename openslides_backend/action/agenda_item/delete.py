from ...models.agenda_item import AgendaItem
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import DeleteAction


@register_action("agenda_item.delete")
class AgendaItemDelete(DeleteAction):
    """
    Action to delete agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_delete_schema()
