import time
from collections import defaultdict
from typing import Any

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.shared.typing import HistoryInformation

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.filters import FilterOperator
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...util.typing import ActionData, ActionResultElement, ActionResults
from .create_base import MotionCreateBase


class BaseMotionCreateForwarded(TextHashMixin, MotionCreateBase):
    """
    Base create action for forwarded motions.
    """

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

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        self.id_to_result_extra_data: dict[int, dict[str, Any]] = {}
        return super().perform(action_data, user_id, internal)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["motions_default_workflow_id", "motions_default_amendment_workflow_id"],
        )
        self.set_state_from_workflow(instance, meeting)
        committee = self.check_for_origin_id(instance)
        self.check_state_allow_forwarding(instance)
        use_original_number = instance.get("use_original_number", False)

        if use_original_submitter := instance.pop("use_original_submitter", False):
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
        self.datastore.apply_changed_model(
            fqid_from_collection_and_id("motion", instance["id"]), instance
        )
        amendment_ids = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["origin_id"]),
            ["amendment_ids"],
        ).get("amendment_ids", [])
        if self.should_forward_amendments(instance):
            new_amendments = self.datastore.get_many(
                [
                    GetManyRequest(
                        "motion",
                        amendment_ids,
                        [
                            "title",
                            "text",
                            "amendment_paragraphs",
                            "reason",
                            "id",
                            "state_id",
                        ],
                    )
                ]
            )["motion"]
            total = len(new_amendments)
            state_ids = {
                state_id
                for amendment in new_amendments.values()
                if (state_id := amendment.get("state_id"))
            }
            if len(state_ids):
                states = self.datastore.get_many(
                    [
                        GetManyRequest(
                            "motion_state", list(state_ids), ["allow_motion_forwarding"]
                        )
                    ]
                )["motion_state"]
            else:
                states = {}
            states = {
                id_: state
                for id_, state in states.items()
                if state.get("allow_motion_forwarding")
            }
            for amendment in list(new_amendments.values()):
                if not (
                    (state_id := amendment.pop("state_id", None)) and state_id in states
                ):
                    new_amendments.pop(amendment["id"])
            amendment_data = new_amendments.values()
            for amendment in amendment_data:
                amendment.update(
                    {
                        "lead_motion_id": instance["id"],
                        "origin_id": amendment["id"],
                        "meeting_id": instance["meeting_id"],
                        "use_original_submitter": use_original_submitter,
                        "use_original_number": use_original_number,
                    }
                )
                amendment.pop("meta_position", 0)
                amendment.pop("id")
            amendment_results = self.create_amendments(list(amendment_data)) or []
            self.id_to_result_extra_data[instance["id"]] = {
                "non_forwarded_amendment_amount": total - len(amendment_results),
                "amendment_result_data": amendment_results,
            }
        else:
            self.id_to_result_extra_data[instance["id"]] = {
                "non_forwarded_amendment_amount": len(amendment_ids),
                "amendment_result_data": [],
            }
        return instance

    def create_amendments(self, amendment_data: ActionData) -> ActionResults | None:
        raise ActionException("Not implemented")

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        result = super().create_action_result_element(instance) or {}
        result.update(self.id_to_result_extra_data.get(result["id"], {}))
        return result

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

    def should_forward_amendments(self, instance: dict[str, Any]) -> bool:
        raise ActionException("Not implemented")

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
