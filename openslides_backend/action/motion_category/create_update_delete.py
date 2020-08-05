from ...models.motion_category import MotionCategory
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("motion_category")
class MotionCategoryActionSet(ActionSet):
    """
    Actions to create, update and delete motion categories.
    """

    model = MotionCategory()
    create_schema = DefaultSchema(MotionCategory()).get_create_schema(
        properties=["name", "prefix", "meeting_id", "parent_id"],
        required_properties=["name", "prefix", "meeting_id"],
    )
    update_schema = DefaultSchema(MotionCategory()).get_update_schema(
        properties=["name", "prefix", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionCategory()).get_delete_schema()
