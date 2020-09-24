from ...models.models import MotionBlock
from ..action_set import ActionSet
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItem,
    agenda_creation_properties,
)
from ..default_schema import DefaultSchema
from ..generics import DeleteAction, UpdateAction
from ..register import register_action_set

create_schema = DefaultSchema(MotionBlock()).get_create_schema(
    properties=["title", "internal", "meeting_id"],
    required_properties=["title", "meeting_id"],
)

create_schema["items"]["properties"].update(agenda_creation_properties)


@register_action_set("motion_block")
class MotionBlockActionSet(ActionSet):
    """
    Actions to create, update and delete motion blocks.
    """

    model = MotionBlock()
    create_schema = create_schema
    update_schema = DefaultSchema(MotionBlock()).get_update_schema(
        properties=["title", "internal", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionBlock()).get_delete_schema()
    routes = {
        "create": CreateActionWithAgendaItem,
        "update": UpdateAction,
        "delete": DeleteAction,
    }
