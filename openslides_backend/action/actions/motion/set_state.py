import time
from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionHelperMixin
from .set_number_mixin import SetNumberMixin


@register_action("motion.set_state")
class MotionSetStateAction(UpdateAction, SetNumberMixin, PermissionHelperMixin):
    """
    Set the state in a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(["state_id"])

    """
        Documentation from Issue1341 locked_fields
        All reading database calls made duringrequest with fqid, origin lock_result
        and changed value, mapped fields and finally calling method name
        00: motion/22, lock=True=>False, mapped:[meeting_id] from get_meeting_id
        01: meeting/222, lock=True=>False, mapped:['is_active_in_organization_id', 'name'] from check_for_archived_meeting
        02: motion/22, lock=True=>False, mapped:['state_id', 'submitter_ids'] from set_state.check permissions
        03: user/1, lock=False, ['group_$222_ids', 'organization_management_level'] => from check_permissions
        04: motion/22, lock=[state_id], mapped_fields:['lead_motion_id', 'category_id', 'number', 'number_value', 'created'] from update_instance
        05: motion_state/77, lock=True=>False, ['next_state_ids', 'previous_state_ids'] from update_instance
        06: meeting/222: lock=True=>False, ['motions_number_type', 'motions_number_min_digits'] from set_number_mixin.set_number
        07: motion_state/76, lock=True=>False, [set_number] from set_number_mixin,set_number
        08: motion_state/76, lock=True=>False, ['set_created_timestamp'] from update_instance
        09: motion_state/76, lock=True=False, [meeting_id] from assert_belongs_to_meeting
        10: motion_state/77, lock=True, [motion_ids] from relation handling
        11: motion_state/76, lock=True, [motion_ids] from relation handling

        All initially locked_fields (and position_number)with my decision whether they have to be locked or not:
        {
            'motion/22/meeting_id': 2, no
            'meeting/222/is_active_in_organization_id': 2, no
            'meeting/222/name': 2, no
            'motion/22/state_id': 2, yes
            'motion/22/submitter_ids': 2, no
            'motion_state/77/next_state_ids': 2, no
            'motion_state/77/previous_state_ids': 2, no
            'meeting/222/motions_number_min_digits': 2, no
            'meeting/222/motions_number_type': 2, no
            'motion_state/76/set_number': 2, no
            'motion_state/76/set_created_timestamp': 2, no
            'motion_state/76/meeting_id': 2, no
            'motion_state/77/motion_ids': 2, yes
            'motion_state/76/motion_ids': 2  yes
        }

        All remaining locked_fields (and position_number) after changes:
            'motion/22/state_id': 2
            'motion_state/77/motion_ids': 2
            'motion_state/76/motion_ids': 2
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the state_id is from a previous or next state.
        """
        motion = self.datastore.get(
            FullQualifiedId(Collection("motion"), instance["id"]),
            [
                "state_id",
                "meeting_id",
                "lead_motion_id",
                "category_id",
                "number",
                "number_value",
                "created",
            ],
            lock_result=["state_id"],
        )
        state_id = motion["state_id"]

        motion_state = self.datastore.get(
            FullQualifiedId(Collection("motion_state"), state_id),
            ["next_state_ids", "previous_state_ids"],
            lock_result=False,
        )
        is_in_next_state_ids = instance["state_id"] in motion_state.get(
            "next_state_ids", []
        )
        is_in_previous_state_ids = instance["state_id"] in motion_state.get(
            "previous_state_ids", []
        )
        if not (is_in_next_state_ids or is_in_previous_state_ids):
            raise ActionException(
                f"State '{instance['state_id']}' is not in next or previous states of the state '{state_id}'."
            )

        self.set_number(
            instance,
            motion["meeting_id"],
            instance["state_id"],
            motion.get("lead_motion_id"),
            motion.get("category_id"),
            motion.get("number"),
            motion.get("number_value"),
        )
        timestamp = round(time.time())
        instance["last_modified"] = timestamp
        if not motion.get("created"):
            state = self.datastore.get(
                FullQualifiedId(Collection("motion_state"), instance["state_id"]),
                ["set_created_timestamp"],
                lock_result=False,
            )
            if state.get("set_created_timestamp"):
                instance["created"] = timestamp
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        motion = self.datastore.get(
            FullQualifiedId(Collection("motion"), instance["id"]),
            [
                "state_id",
                "submitter_ids",
                "meeting_id",
            ],
            lock_result=False,
        )
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_MANAGE_METADATA,
            motion["meeting_id"],
        ):
            return

        if self.is_allowed_and_submitter(
            motion.get("submitter_ids", []), motion["state_id"]
        ):
            return

        raise MissingPermission(Permissions.Motion.CAN_MANAGE_METADATA)
