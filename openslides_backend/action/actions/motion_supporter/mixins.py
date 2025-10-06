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
        if not self.is_self_instance(instance) or not len(
            self.check_perm_and_delegator_restriction(
                Permissions.Motion.CAN_MANAGE_METADATA,
                "users_forbid_delegator_as_supporter",
                [self.get_meeting_id(instance)],
            )
        ):
            meeting_id = self.get_meeting_id(instance)
            if has_perm(
                self.datastore,
                self.user_id,
                Permissions.Motion.CAN_SUPPORT,
                meeting_id,
            ):
                return
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

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        motion_get_many_request = GetManyRequest(
            "motion",
            [self.get_motion_id(instance) for instance in action_data],
            ["meeting_id", "state_id", "supporter_ids"],
        )
        gm_motion_result = self.datastore.get_many([motion_get_many_request])
        motions = gm_motion_result.get("motion", {})
        meeting_ids = []
        for key in motions:
            if not motions[key]["meeting_id"] in meeting_ids:
                meeting_ids.append(motions[key]["meeting_id"])
        gm_request_meeting = GetManyRequest(
            "meeting", meeting_ids, ["motions_supporters_min_amount"]
        )
        state_ids = []
        for key in motions:
            if not motions[key]["state_id"] in state_ids:
                state_ids.append(motions[key]["state_id"])
        gm_request_state = GetManyRequest("motion_state", state_ids, ["allow_support"])
        gm_result = self.datastore.get_many([gm_request_meeting, gm_request_state])
        for instance in action_data:
            motion = motions.get(self.get_motion_id(instance), {})
            meeting_id = motion.get("meeting_id")
            if meeting_id is None:
                raise ActionException("Motion is missing meeting_id.")
            if not has_perm(
                self.datastore, self.user_id, Permissions.Motion.CAN_MANAGE, meeting_id
            ):
                meeting = gm_result.get("meeting", {}).get(meeting_id, {})
                if meeting.get("motions_supporters_min_amount") == 0:
                    # TODO: Perhaps this should be moved out of the if clause
                    raise ActionException("Motion supporters system deactivated.")
                state_id = motion.get("state_id")
                if state_id is None:
                    raise ActionException("Motion is missing state_id.")
                state = gm_result.get("motion_state", {}).get(state_id, {})

                if state.get("allow_support") is False:
                    raise ActionException("The state does not allow support.")
        return action_data
