from typing import Any

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, BadCodingException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.delegation_based_restriction_mixin import DelegationBasedRestrictionMixin
from ...util.typing import ActionData


class SupporterActionMixin(DelegationBasedRestrictionMixin):
    permission = Permissions.Motion.CAN_MANAGE_METADATA

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if self.is_self_instance(instance):
            if not len(
                self.check_perm_and_delegator_restriction(
                    Permissions.Motion.CAN_MANAGE_METADATA,
                    "users_forbid_delegator_as_supporter",
                    [self.get_meeting_id(instance)],
                )
            ):
                meeting_id = self.get_meeting_id(instance)
                if not has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.Motion.CAN_SUPPORT,
                    meeting_id,
                ):
                    raise MissingPermission(Permissions.Motion.CAN_SUPPORT)
        else:
            super().check_permissions(instance)

    def get_motion_id(self, instance: dict[str, Any]) -> int:
        raise BadCodingException("get_motion_id not implemented.")

    def get_meeting_user_id(self, instance: dict[str, Any]) -> int | None:
        raise BadCodingException("get_meeting_user_id not implemented.")

    def is_self_instance(self, instance: dict[str, Any]) -> bool:
        meeting_user_id = self.get_meeting_user_id(instance)
        if meeting_user_id:
            return (
                self.datastore.get(
                    fqid_from_collection_and_id("meeting_user", meeting_user_id),
                    ["user_id"],
                )["user_id"]
                == self.user_id
            )
        return False

    def check_action_data(self, action_data: ActionData) -> ActionData:
        motion_get_many_request = GetManyRequest(
            "motion",
            [self.get_motion_id(instance) for instance in action_data],
            ["meeting_id", "state_id", "supporter_ids"],
        )
        gm_motion_result = self.datastore.get_many([motion_get_many_request])
        motions = gm_motion_result.get("motion", {})
        meeting_ids = list({motions[key]["meeting_id"] for key in motions})
        gm_request_meeting = GetManyRequest(
            "meeting", meeting_ids, ["motions_supporters_min_amount"]
        )
        state_ids = list({motions[key]["state_id"] for key in motions})
        gm_request_state = GetManyRequest("motion_state", state_ids, ["allow_support"])
        gm_result = self.datastore.get_many([gm_request_meeting, gm_request_state])
        for instance in action_data:
            motion = motions.get(self.get_motion_id(instance), {})
            meeting_id = motion["meeting_id"]
            meeting = gm_result.get("meeting", {}).get(meeting_id, {})
            if meeting.get("motions_supporters_min_amount") == 0:
                raise ActionException("Motion supporters system deactivated.")
            if not has_perm(
                self.datastore,
                self.user_id,
                Permissions.Motion.CAN_MANAGE_METADATA,
                meeting_id,
            ):
                state = gm_result.get("motion_state", {}).get(motion["state_id"], {})

                if state.get("allow_support") is False:
                    raise ActionException("The state does not allow support.")
        return action_data
