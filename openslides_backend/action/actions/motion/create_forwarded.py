from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_base import MotionCreateBase
from .update_all_derived_motion_ids import MotionUpdateAllDerivedMotionIds


@register_action("motion.create_forwarded")
class MotionCreateForwarded(MotionCreateBase):
    """
    Create action for forwarded motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "reason",
        ],
        required_properties=["meeting_id", "title", "text", "origin_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            [
                "motions_default_workflow_id",
            ],
        )
        self.set_state_from_workflow(instance, meeting)
        self.check_for_origin_id(instance)
        self.create_submitters(instance)
        self.set_sequential_number(instance)
        self.set_created_last_modified_and_number(instance)
        self.calculate_all_origin_ids_and_all_derived_motion_ids(instance)
        return instance

    def check_for_origin_id(self, instance: Dict[str, Any]) -> None:
        if instance.get("origin_id"):
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
                ["committee_id"],
            )
            forwarded_from = self.datastore.get(
                FullQualifiedId(Collection("motion"), instance["origin_id"]),
                ["meeting_id"],
            )
            forwarded_from_meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), forwarded_from["meeting_id"]),
                ["committee_id"],
            )
            committee = self.datastore.get(
                FullQualifiedId(
                    Collection("committee"), forwarded_from_meeting["committee_id"]
                ),
                ["forward_to_committee_ids"],
            )
            if meeting["committee_id"] not in committee.get(
                "forward_to_committee_ids", []
            ):
                raise ActionException(
                    f"Committee id {meeting['committee_id']} not in {committee.get('forward_to_committee_ids', [])}"
                )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        perm = Permissions.Motion.CAN_FORWARD_INTO_THIS_MEETING
        if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {perm}"
            raise PermissionDenied(msg)

        origin = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["origin_id"]),
            ["meeting_id"],
        )
        perm_origin = Permissions.Motion.CAN_MANAGE
        if not has_perm(
            self.datastore, self.user_id, perm_origin, origin["meeting_id"]
        ):
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {perm_origin}"
            raise PermissionDenied(msg)

        # check if origin motion is amendment or statute_amendment
        origin = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["origin_id"]),
            ["lead_motion_id", "statute_paragraph_id"],
        )
        if origin.get("lead_motion_id") or origin.get("statute_paragraph_id"):
            msg = "Amendments cannot be forwarded."
            raise PermissionDenied(msg)

    def calculate_all_origin_ids_and_all_derived_motion_ids(
        self, instance: Dict[str, Any]
    ) -> None:
        instance["all_derived_motion_ids"] = []
        if instance.get("origin_id"):
            origin = self.datastore.get(
                FullQualifiedId(Collection("motion"), instance["origin_id"]),
                ["all_origin_ids"],
            )
            instance["all_origin_ids"] = origin.get("all_origin_ids", [])
            instance["all_origin_ids"].append(instance["origin_id"])
        else:
            instance["all_origin_ids"] = []

        # Update the all_derived_motion_ids of the origins
        action_data = []
        for origin_id in instance["all_origin_ids"]:
            origin = self.datastore.get(
                FullQualifiedId(Collection("motion"), origin_id),
                ["all_derived_motion_ids"],
            )
            action_data.append(
                {
                    "id": origin_id,
                    "all_derived_motion_ids": origin.get("all_derived_motion_ids", [])
                    + [instance["id"]],
                }
            )
        if action_data:
            self.execute_other_action(MotionUpdateAllDerivedMotionIds, action_data)
