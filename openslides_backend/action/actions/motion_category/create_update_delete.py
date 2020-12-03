from ....models.models import MotionCategory
from ...action_set import ActionSet
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


@register_action_set("motion_category")
class MotionCategoryActionSet(ActionSet):
    """
    Actions to create, update and delete motion categories.
    """

    model = MotionCategory()
    create_schema = DefaultSchema(MotionCategory()).get_create_schema(
        required_properties=["name", "prefix", "meeting_id"],
        optional_properties=["parent_id"],
    )
    update_schema = DefaultSchema(MotionCategory()).get_update_schema(
        optional_properties=["name", "prefix", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionCategory()).get_delete_schema()
