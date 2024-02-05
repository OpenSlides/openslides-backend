from typing import Any

from ....models.models import MotionSubmitter
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...mixins.weight_mixin import WeightMixin
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_submitter.create")
class MotionSubmitterCreateAction(
    WeightMixin, CreateActionWithInferredMeetingMixin, CreateAction
):
    """
    Action to create a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_create_schema(
        required_properties=["motion_id", "meeting_user_id"],
        optional_properties=["weight"],
    )
    history_information = "Submitters changed"
    history_relation_field = "motion_id"
    permission = Permissions.Motion.CAN_MANAGE_METADATA

    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Check if motion and user belong to the same meeting.
        """
        instance = self.update_instance_with_meeting_id(instance)
        meeting_id = instance["meeting_id"]  # meeting_id is set from motion

        meeting_user = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["meeting_user_id"]),
            ["user_id"],
        )
        if not has_organization_management_level(
            self.datastore,
            meeting_user["user_id"],
            OrganizationManagementLevel.SUPERADMIN,
        ):
            assert_belongs_to_meeting(
                self.datastore,
                [fqid_from_collection_and_id("user", meeting_user["user_id"])],
                meeting_id,
            )

        filter = And(
            FilterOperator("meeting_user_id", "=", instance["meeting_user_id"]),
            FilterOperator("motion_id", "=", instance["motion_id"]),
            FilterOperator("meeting_id", "=", meeting_id),
        )
        exists = self.datastore.exists(collection=self.model.collection, filter=filter)
        if exists:
            raise ActionException("(meeting_user_id, motion_id) must be unique.")
        if instance.get("weight") is None:
            filter = And(
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
                FilterOperator("motion_id", "=", instance["motion_id"]),
            )
            instance["weight"] = self.get_weight(filter)
        return instance
