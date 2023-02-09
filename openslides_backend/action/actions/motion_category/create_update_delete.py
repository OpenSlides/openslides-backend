from typing import Any, Dict

from ....models.models import MotionCategory
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ...action import Action
from ...action_set import ActionSet
from ...generics.update import UpdateAction
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class PrefixUniqueMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if instance.get("prefix"):
            meeting_id = self.get_meeting_id(instance)
            if self.datastore.exists(
                "motion_category",
                And(
                    FilterOperator("prefix", "=", instance["prefix"]),
                    FilterOperator("id", "!=", instance["id"]),
                    FilterOperator("meeting_id", "=", meeting_id),
                ),
            ):
                raise ActionException(
                    f"Prefix '{instance['prefix']}' is not unique in the meeting."
                )
        return instance


class MotionCategoryCreate(PrefixUniqueMixin, SequentialNumbersMixin):
    pass


class MotionCategoryUpdate(PrefixUniqueMixin, UpdateAction):
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
    UpdateActionClass = MotionCategoryUpdate
