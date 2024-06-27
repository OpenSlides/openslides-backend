import time
from collections import defaultdict
from typing import Any

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .create_base import MotionCreateBase


@register_action("motion.create_forwarded")
class MotionCreateForwarded(TextHashMixin, MotionCreateBase):
    """
    Create action for forwarded motions.
    """

    schema = DefaultSchema(Motion()).get_create_schema(
        required_properties=["meeting_id", "title", "text", "origin_id"],
        optional_properties=["reason"],
        additional_optional_fields={
            "use_original_submitter": {"type": "boolean"},
            "use_original_number": {"type": "boolean"},
        },
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

    def get_user_verbose_names(self, meeting_user_ids: list[int]) -> str | None:
        meeting_users = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user", meeting_user_ids, ["user_id", "structure_level_ids"]
                )
            ]
        )["meeting_user"]
        user_ids = [
            user_id
            for meeting_user in meeting_users.values()
            if (user_id := meeting_user.get("user_id"))
        ]
        if not len(user_ids):
            return None
        requests = [
            GetManyRequest(
                "user", user_ids, ["id", "first_name", "last_name", "title", "pronoun"]
            )
        ]
        if structure_level_ids := list(
            {
                structure_level_id
                for meeting_user in meeting_users.values()
                for structure_level_id in meeting_user.get("structure_level_ids", [])
            }
        ):
            requests.append(
                GetManyRequest("structure_level", structure_level_ids, ["name"])
            )
        user_data = self.datastore.get_many(requests)
        users = user_data["user"]
        structure_levels = user_data["structure_level"]
        names = []
        for meeting_user_id in meeting_user_ids:
            meeting_user = meeting_users[meeting_user_id]
            user = users.get(meeting_user.get("user_id", 0))
            if user:
                additional_info: list[str] = []
                if pronoun := user.get("pronoun"):
                    additional_info = [pronoun]
                if sl_ids := meeting_user.get("structure_level_ids"):
                    if slnames := ", ".join(
                        name
                        for structure_level_id in sl_ids
                        if (
                            name := structure_levels.get(structure_level_id, {}).get(
                                "name"
                            )
                        )
                    ):
                        additional_info.append(slnames)
                suffix = " · ".join(additional_info)
                if suffix:
                    suffix = f"({suffix})"
                if not any(user.get(field) for field in ["first_name", "last_name"]):
                    short_name = f"User {user['id']}"
                else:
                    short_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                long_name = f"{user.get('title', '')} {short_name} {suffix}".strip()
                names.append(long_name)
        return ", ".join(names)

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

        if instance.pop("use_original_submitter", None):
            submitters = list(
                self.datastore.filter(
                    "motion_submitter",
                    FilterOperator("motion_id", "=", instance["origin_id"]),
                    ["meeting_user_id"],
                ).values()
            )
            submitters = sorted(submitters, key=lambda x: x.get("weight", 10000))
            meeting_user_ids = [
                meeting_user_id
                for submitter in submitters
                if (meeting_user_id := submitter.get("meeting_user_id"))
            ]
            if len(meeting_user_ids):
                instance["additional_submitter"] = self.get_user_verbose_names(
                    meeting_user_ids
                )
            text_submitter = self.datastore.get(
                fqid_from_collection_and_id("motion", instance["origin_id"]),
                ["additional_submitter"],
            ).get("additional_submitter")
            if text_submitter:
                if instance.get("additional_submitter"):
                    instance["additional_submitter"] += ", " + text_submitter
                else:
                    instance["additional_submitter"] = text_submitter
        else:
            name = committee.get("name", f"Committee {committee['id']}")
            instance["additional_submitter"] = name

        self.set_sequential_number(instance)
        self.handle_number(instance)
        self.set_origin_ids(instance)
        self.set_text_hash(instance)
        instance["forwarded"] = round(time.time())
        return instance

    def handle_number(self, instance: dict[str, Any]) -> dict[str, Any]:
        origin = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["origin_id"]), ["number"]
        )
        if instance.pop("use_original_number", None) and (num := origin.get("number")):
            number = self.get_clean_number(num, instance["meeting_id"])
            self.set_created_last_modified(instance)
            instance["number"] = number
        else:
            self.set_created_last_modified_and_number(instance)
        return instance

    def get_clean_number(self, number: str, meeting_id: int) -> str:
        new_number = number
        next_identifier = 1
        while not self._check_if_unique(new_number, meeting_id, None):
            new_number = f"{number}-{next_identifier}"
            next_identifier += 1
        return new_number

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
            ["id", "name", "forward_to_committee_ids"],
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
