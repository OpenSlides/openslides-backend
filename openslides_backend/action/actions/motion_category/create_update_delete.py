from typing import Any

from ....models.models import MotionCategory
from ....permissions.permissions import Permissions
from ....shared.filters import FilterOperator
from ...action_set import ActionSet
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class MotionCategoryCreate(SequentialNumbersMixin, WeightMixin):
    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance["weight"] = self.get_weight(
            FilterOperator("meeting_id", "=", instance["meeting_id"])
        )
        return super().update_instance(instance)


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
