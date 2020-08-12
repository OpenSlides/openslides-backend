from ...models.motion_state import MotionState
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("motion_state")
class MotionStateActionSet(ActionSet):
    """
    Actions to create, update and delete motion states.
    """

    model = MotionState()
    create_schema = DefaultSchema(MotionState()).get_create_schema(
        properties=["name"], required_properties=["name"],
    )
    update_schema = DefaultSchema(MotionState()).get_update_schema(properties=["name"])
    delete_schema = DefaultSchema(MotionState()).get_delete_schema()
