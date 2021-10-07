from typing import Any, Dict

from ....models.models import MotionSubmitter
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("motion_submitter.create")
class MotionSubmitterCreateAction(CreateActionWithInferredMeetingMixin, CreateAction):
    """
    Action to create a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_create_schema(
        required_properties=["motion_id", "user_id"],
        optional_properties=["weight"],
    )
    permission = Permissions.Motion.CAN_MANAGE_METADATA

    relation_field_for_meeting = "motion_id"
    weight_map: Dict[int, int] = {}

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.weight_map = {}
        return super().get_updated_instances(action_data)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if motion and user belong to the same meeting.
        """
        instance = self.update_instance_with_meeting_id(instance)
        meeting_id = instance["meeting_id"]  # meeting_id is set from motion
        if not has_organization_management_level(
            self.datastore, instance["user_id"], OrganizationManagementLevel.SUPERADMIN
        ):
            assert_belongs_to_meeting(
                self.datastore,
                [FullQualifiedId(Collection("user"), instance["user_id"])],
                meeting_id,
            )

        # check, if (user_id, motion_id) already in the datastore.
        filter = And(
            FilterOperator("user_id", "=", instance["user_id"]),
            FilterOperator("motion_id", "=", instance["motion_id"]),
        )
        exists = self.datastore.exists(collection=self.model.collection, filter=filter)
        if exists:
            raise ActionException("(user_id, motion_id) must be unique.")
        if instance.get("weight") is None:
            self.set_weight(instance)
        return instance

    def set_weight(self, instance: Dict[str, Any]) -> None:
        motion_id = instance["motion_id"]
        if motion_id in self.weight_map:
            max_weight = self.weight_map[motion_id]
            self.weight_map[motion_id] += 1
        else:
            filter_ = FilterOperator("motion_id", "=", motion_id)
            max_weight = (
                self.datastore.max(self.model.collection, filter_, "weight", "int") or 0
            )
            self.weight_map[motion_id] = max_weight + 1
        instance["weight"] = max_weight + 1
