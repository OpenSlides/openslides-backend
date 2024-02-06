import time
from typing import Any

from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionHelperMixin, set_workflow_timestamp_helper
from .motion_state_history_information_mixin import MotionStateHistoryInformationMixin
from .set_number_mixin import SetNumberMixin


@register_action("motion.set_state")
class MotionSetStateAction(
    UpdateAction,
    SetNumberMixin,
    PermissionHelperMixin,
    MotionStateHistoryInformationMixin,
):
    """
    Set the state in a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(["state_id"])

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Check if the state_id is from a previous or next state.
        """
        fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        motion = self.datastore.get(
            fqid,
            [
                "state_id",
                "meeting_id",
                "lead_motion_id",
                "category_id",
                "number",
                "number_value",
                "workflow_timestamp",
            ],
            lock_result=["state_id"],
        )
        self.apply_instance(motion, fqid)
        state_id = motion["state_id"]

        if not self.skip_state_graph_check:
            motion_state = self.datastore.get(
                fqid_from_collection_and_id("motion_state", state_id),
                ["next_state_ids", "previous_state_ids"],
                lock_result=False,
            )
            if instance["state_id"] not in (
                motion_state.get("next_state_ids", [])
                + motion_state.get("previous_state_ids", [])
            ):
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
        if not motion.get("workflow_timestamp"):
            set_workflow_timestamp_helper(self.datastore, instance, timestamp)
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.skip_state_graph_check = False
        motion = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["id"]),
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
            self.skip_state_graph_check = True
            return

        if self.is_submitter(motion.get("submitter_ids", [])) and has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_SEE,
            motion["meeting_id"],
        ):
            state = self.datastore.get(
                fqid_from_collection_and_id("motion_state", motion["state_id"]),
                ["submitter_withdraw_state_id"],
            )
            if instance["state_id"] == state.get("submitter_withdraw_state_id"):
                self.skip_state_graph_check = True
                return

        if self.is_allowed_and_submitter(
            motion.get("submitter_ids", []), motion["state_id"]
        ):
            return

        raise MissingPermission(Permissions.Motion.CAN_MANAGE_METADATA)

    def get_history_information(self) -> HistoryInformation | None:
        return self._get_state_history_information("state_id", "State")
