import time
from collections import defaultdict
from typing import Any

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_user.create import MeetingUserCreate
from ..meeting_user.update import MeetingUserUpdate
from ..user.create import UserCreate
from .create_base import MotionCreateBase


@register_action("motion.create_forwarded")
class MotionCreateForwarded(TextHashMixin, MotionCreateBase):
    """
    Create action for forwarded motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        required_properties=["meeting_id", "title", "text", "origin_id"],
        optional_properties=["reason"],
    )

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(
                        {
                            meeting_id
                            for instance in action_data
                            if (meeting_id := instance.get("meeting_id"))
                        }
                    ),
                    [
                        "id",
                        "is_active_in_organization_id",
                        "name",
                        "motions_default_workflow_id",
                        "committee_id",
                        "default_group_id",
                        "motion_submitter_ids",
                        "motions_number_type",
                        "motions_number_min_digits",
                        "agenda_item_creation",
                        "list_of_speakers_initially_closed",
                        "list_of_speakers_ids",
                        "motion_ids",
                    ],
                ),
                GetManyRequest(
                    "motion",
                    list(
                        {
                            origin_id
                            for instance in action_data
                            if (origin_id := instance.get("origin_id"))
                        }
                    ),
                    [
                        "meeting_id",
                        "lead_motion_id",
                        "statute_paragraph_id",
                        "state_id",
                        "all_origin_ids",
                        "derived_motion_ids",
                        "all_derived_motion_ids",
                    ],
                ),
            ]
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            [
                "motions_default_workflow_id",
            ],
        )
        self.set_state_from_workflow(instance, meeting)
        committee = self.check_for_origin_id(instance)
        self.check_state_allow_forwarding(instance)

        # handle forwarding user
        target_meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["id", "default_group_id"],
        )
        if committee.get("forwarding_user_id"):
            forwarding_user_id = committee["forwarding_user_id"]
            meeting_id = instance["meeting_id"]
            forwarding_user_groups = self.get_groups_from_meeting_user(
                meeting_id, forwarding_user_id
            )
            if target_meeting["default_group_id"] not in forwarding_user_groups:
                meeting_user = self.get_meeting_user(
                    meeting_id, forwarding_user_id, ["id", "group_ids"]
                )
                if not meeting_user:
                    self.execute_other_action(
                        MeetingUserCreate,
                        [
                            {
                                "meeting_id": meeting_id,
                                "user_id": forwarding_user_id,
                                "group_ids": [target_meeting["default_group_id"]],
                            }
                        ],
                    )
                else:
                    self.execute_other_action(
                        MeetingUserUpdate,
                        [
                            {
                                "id": meeting_user["id"],
                                "group_ids": (meeting_user.get("group_ids") or [])
                                + [target_meeting["default_group_id"]],
                            }
                        ],
                    )

        else:
            username = committee.get("name", "Committee User")
            meeting_id = instance["meeting_id"]
            committee_user_create_payload = {
                "last_name": username,
                "is_physical_person": False,
                "is_active": False,
                "forwarding_committee_ids": [committee["id"]],
            }
            action_result = self.execute_other_action(
                UserCreate, [committee_user_create_payload], skip_history=True
            )
            assert action_result and action_result[0]
            forwarding_user_id = action_result[0]["id"]
            self.execute_other_action(
                MeetingUserCreate,
                [
                    {
                        "user_id": forwarding_user_id,
                        "meeting_id": meeting_id,
                        "group_ids": [target_meeting["default_group_id"]],
                    }
                ],
            )
        instance["submitter_ids"] = [forwarding_user_id]

        self.create_submitters(instance)
        self.set_sequential_number(instance)
        self.set_created_last_modified_and_number(instance)
        self.set_origin_ids(instance)
        self.set_text_hash(instance)
        instance["forwarded"] = round(time.time())
        return instance

    def check_for_origin_id(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["committee_id"],
        )
        forwarded_from = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["origin_id"]),
            ["meeting_id"],
        )
        forwarded_from_meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", forwarded_from["meeting_id"]),
            ["committee_id"],
        )
        # use the forwarding user id and id later in the handle forwarding user
        # code.
        committee = self.datastore.get(
            fqid_from_collection_and_id(
                "committee", forwarded_from_meeting["committee_id"]
            ),
            ["id", "name", "forward_to_committee_ids", "forwarding_user_id"],
        )
        if meeting["committee_id"] not in committee.get("forward_to_committee_ids", []):
            raise ActionException(
                f"Committee id {meeting['committee_id']} not in {committee.get('forward_to_committee_ids', [])}"
            )
        return committee

    def check_permissions(self, instance: dict[str, Any]) -> None:
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["meeting_id"],
            lock_result=False,
        )
        perm_origin = Permissions.Motion.CAN_FORWARD
        if not has_perm(
            self.datastore, self.user_id, perm_origin, origin["meeting_id"]
        ):
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {perm_origin}"
            raise PermissionDenied(msg)

        # check if origin motion is amendment or statute_amendment
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["lead_motion_id", "statute_paragraph_id"],
            lock_result=False,
        )
        if origin.get("lead_motion_id") or origin.get("statute_paragraph_id"):
            msg = "Amendments cannot be forwarded."
            raise PermissionDenied(msg)

    def set_origin_ids(self, instance: dict[str, Any]) -> None:
        if instance.get("origin_id"):
            origin = self.datastore.get(
                fqid_from_collection_and_id("motion", instance["origin_id"]),
                ["all_origin_ids", "meeting_id"],
            )
            instance["origin_meeting_id"] = origin["meeting_id"]
            instance["all_origin_ids"] = origin.get("all_origin_ids", [])
            instance["all_origin_ids"].append(instance["origin_id"])

    def check_state_allow_forwarding(self, instance: dict[str, Any]) -> None:
        origin = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["origin_id"]),
            ["state_id"],
        )
        state = self.datastore.get(
            fqid_from_collection_and_id("motion_state", origin["state_id"]),
            ["allow_motion_forwarding"],
        )
        if not state.get("allow_motion_forwarding"):
            raise ActionException("State doesn't allow to forward motion.")

    def get_history_information(self) -> HistoryInformation | None:
        forwarded_entries = defaultdict(list)
        for instance in self.instances:
            forwarded_entries[
                fqid_from_collection_and_id("motion", instance["origin_id"])
            ].extend(
                [
                    "Forwarded to {}",
                    fqid_from_collection_and_id("meeting", instance["meeting_id"]),
                ]
            )
        return forwarded_entries | {
            fqid_from_collection_and_id("motion", instance["id"]): [
                "Motion created (forwarded)"
            ]
            for instance in self.instances
        }
