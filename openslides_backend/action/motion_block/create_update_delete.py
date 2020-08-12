from ...models.motion_block import MotionBlock
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("motion_block")
class MotionBlockActionSet(ActionSet):
    """
    Actions to create, update and delete motion blocks.
    """

    model = MotionBlock()
    create_schema = DefaultSchema(MotionBlock()).get_create_schema(
        properties=["title", "internal", "meeting_id"], required_properties=["title"],
    )
    update_schema = DefaultSchema(MotionBlock()).get_update_schema(
        properties=["title", "internal", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionBlock()).get_delete_schema()
