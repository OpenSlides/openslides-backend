from typing import Any, Dict

from ....models.models import MotionSubmitter
from ....permissions.management_levels import OrganisationManagementLevel
from ....permissions.permission_helper import has_organisation_management_level
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


@register_action("motion_submitter.create")
class MotionSubmitterCreateAction(CreateActionWithInferredMeetingMixin, CreateAction):
    """
    Action to create a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_create_schema(
        ["motion_id", "user_id"],
    )
    permission = Permissions.Motion.CAN_MANAGE_METADATA

    relation_field_for_meeting = "motion_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if motion and user belong to the same meeting if the user is a temporary user.
        """
        instance = self.update_instance_with_meeting_id(instance)
        meeting_id = instance["meeting_id"]  # meeting_id is set from motion
        if not has_organisation_management_level(
            self.datastore, instance["user_id"], OrganisationManagementLevel.SUPERADMIN
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
        return instance
