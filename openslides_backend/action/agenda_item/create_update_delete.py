from ...models.agenda_item import AgendaItem
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from .create import AgendaItemCreate, create_agenda_item_schema
from .update import AgendaItemUpdate, update_agenda_item_schema


@register_action_set("agenda_item")
class AgendaItemActionSet(ActionSet):
    """
    Actions to create, update and delete motion workflows.
    """

    model = AgendaItem()
    create_schema = create_agenda_item_schema
    update_schema = update_agenda_item_schema
    delete_schema = DefaultSchema(AgendaItem()).get_delete_schema()
    routes = {
        "create": AgendaItemCreate,
        "delete": DeleteAction,
        "update": AgendaItemUpdate,
    }
