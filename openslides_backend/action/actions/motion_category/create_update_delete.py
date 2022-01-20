from ....models.models import MotionCategory
from ....permissions.permissions import Permissions
from ...action_set import ActionSet
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class MotionCategoryCreate(SequentialNumbersMixin):
    pass


@register_action_set("motion_category")
class MotionCategoryActionSet(ActionSet):
    """
    Actions to create, update and delete motion categories.
    """

    model = MotionCategory()
    create_schema = DefaultSchema(MotionCategory()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["parent_id", "prefix"],
    )
    update_schema = DefaultSchema(MotionCategory()).get_update_schema(
        optional_properties=["name", "prefix", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionCategory()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE
    CreateActionClass = MotionCategoryCreate
