from typing import Any

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...mixins.delegation_based_restriction_mixin import DelegationBasedRestrictionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_user.helper_mixin import MeetingUserHelperMixin


@register_action("motion.set_support_self")
class MotionSetSupportSelfAction(
    MeetingUserHelperMixin, DelegationBasedRestrictionMixin, UpdateAction
):
    """
    Action to add the user to the support of a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_default_schema(
        title="Schema for set support self",
        description="motion_id is a required id and support is a boolean.",
        additional_required_fields={
            "motion_id": required_id_schema,
            "support": {"type": "boolean"},
        },
    )
    permission_id = "motion_id"
    permission = Permissions.Motion.CAN_SUPPORT

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if not len(
            self.check_perm_and_delegator_restriction(
                Permissions.Motion.CAN_MANAGE,
                "users_forbid_delegator_as_supporter",
                [self.get_meeting_id(instance)],
            )
        ):
            return super().check_permissions(instance)

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        motion_get_many_request = GetManyRequest(
            self.model.collection,
            [instance["motion_id"] for instance in action_data],
            ["meeting_id", "state_id", "supporter_meeting_user_ids"],
        )
        gm_motion_result = self.datastore.get_many([motion_get_many_request])
        motions = gm_motion_result.get(self.model.collection, {})
        meeting_ids = []
        for key in motions:
            if not motions[key]["meeting_id"] in meeting_ids:
                meeting_ids.append(motions[key]["meeting_id"])
        state_ids = []
        for key in motions:
            if not motions[key]["state_id"] in state_ids:
                state_ids.append(motions[key]["state_id"])
        gm_request_meeting = GetManyRequest(
            "meeting", meeting_ids, ["motions_supporters_min_amount"]
        )
        gm_request_state = GetManyRequest("motion_state", state_ids, ["allow_support"])
        gm_result = self.datastore.get_many([gm_request_meeting, gm_request_state])
        for instance in action_data:
            motion = motions.get(instance["motion_id"], {})
            meeting_id = motion.get("meeting_id")
            if meeting_id is None:
                raise ActionException("Motion is missing meeting_id.")
            meeting = gm_result.get("meeting", {}).get(meeting_id, {})
            if meeting.get("motions_supporters_min_amount") == 0:
                raise ActionException("Motion supporters system deactivated.")
            state_id = motion.get("state_id")
            if state_id is None:
                raise ActionException("Motion is missing state_id.")
            state = gm_result.get("motion_state", {}).get(state_id, {})

            if state.get("allow_support") is False:
                raise ActionException("The state does not allow support.")

            supporter_meeting_user_ids = motion.get("supporter_meeting_user_ids", [])
            changed = False
            motion_id = instance.pop("motion_id")
            support = instance.pop("support")
            meeting_user_id = self.create_or_get_meeting_user(
                motion["meeting_id"], self.user_id
            )
            if support:
                if meeting_user_id not in supporter_meeting_user_ids:
                    supporter_meeting_user_ids.append(meeting_user_id)
                    changed = True
            else:
                if meeting_user_id in supporter_meeting_user_ids:
                    supporter_meeting_user_ids.remove(meeting_user_id)
                    changed = True
            instance["id"] = motion_id
            if changed:
                instance["supporter_meeting_user_ids"] = supporter_meeting_user_ids
                yield instance
