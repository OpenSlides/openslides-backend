from ....models.models import AgendaItem
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("agenda_item.delete")
class AgendaItemDelete(DeleteAction):
    """
    Action to delete agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_delete_schema()
    permission_description = "agenda.can_manage"
