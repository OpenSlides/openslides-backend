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
from ...mixins.forward_mediafiles_mixin import ForwardMediafilesMixin
from ...util.typing import ActionData, ActionResultElement, ActionResults
from ..motion_change_recommendation.create import MotionChangeRecommendationCreateAction
from .create_base import MotionCreateBase


class BaseMotionCreateForwarded(
    ForwardMediafilesMixin, TextHashMixin, MotionCreateBase
):
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
                        "motions_default_amendment_workflow_id",
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
                        "state_id",
                        "all_origin_ids",
                        "derived_motion_ids",
                        "all_derived_motion_ids",
                        "amendment_ids",
                        "attachment_meeting_mediafile_ids",
                    ],
                ),
            ],
            lock_result=False,
        )

    def get_user_verbose_names(self, meeting_user_ids: list[int]) -> str | None:
        meeting_users = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user", meeting_user_ids, ["user_id", "structure_level_ids"]
                )
            ],
            lock_result=False,
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
        user_data = self.datastore.get_many(requests, lock_result=False)
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
        self.with_attachments = instance.pop("with_attachments", False)
        self.mark_amendments = instance.pop(
            "mark_amendments_as_forwarded", False
        ) or instance.get("marked_forwarded", False)
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["motions_default_workflow_id", "motions_default_amendment_workflow_id"],
            lock_result=False,
        )
        self.set_state_from_workflow(instance, meeting)
        committee = self.check_for_origin_id(instance)
        use_original_number = instance.get("use_original_number", False)

        if use_original_submitter := instance.pop("use_original_submitter", False):
            submitters = list(
                self.datastore.filter(
                    "motion_submitter",
                    FilterOperator("motion_id", "=", instance["origin_id"]),
                    ["meeting_user_id"],
                    lock_result=False,
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
                lock_result=False,
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
        with_change_recommendations = instance.pop("with_change_recommendations", False)
        self.datastore.apply_changed_model(
            fqid_from_collection_and_id("motion", instance["id"]), instance
        )
        if with_change_recommendations:
            change_recos = self.datastore.filter(
                "motion_change_recommendation",
                FilterOperator("motion_id", "=", instance["origin_id"]),
                [
                    "rejected",
                    "internal",
                    "type",
                    "other_description",
                    "line_from",
                    "line_to",
                    "text",
                ],
            )
            change_reco_data = [
                {**change_reco, "motion_id": instance["id"]}
                for change_reco in change_recos.values()
            ]
            self.execute_other_action(
                MotionChangeRecommendationCreateAction, change_reco_data
            )
        amendment_ids = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["origin_id"]),
            ["amendment_ids"],
            lock_result=False,
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
                            "motion_state",
                            list(state_ids),
                            ["allow_amendment_forwarding"],
                        )
                    ],
                    lock_result=False,
                )["motion_state"]
            else:
                states = {}
            states = {
                id_: state
                for id_, state in states.items()
                if state.get("allow_amendment_forwarding")
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
                        "with_change_recommendations": with_change_recommendations,
                        "marked_forwarded": self.mark_amendments,
                        "with_attachments": self.with_attachments,
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
        if self.with_attachments:
            self.forward_mediafiles(
                instance, getattr(self, "meeting_mediafile_replace_map", {})
            )
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
            fqid_from_collection_and_id("motion", instance["origin_id"]),
            ["number"],
            lock_result=False,
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
            lock_result=False,
        )
        forwarded_from = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["origin_id"]),
            ["meeting_id"],
            lock_result=False,
        )
        forwarded_from_meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", forwarded_from["meeting_id"]),
            ["committee_id"],
            lock_result=False,
        )
        # use the forwarding user id and id later in the handle forwarding user
        # code.
        committee = self.datastore.get(
            fqid_from_collection_and_id(
                "committee", forwarded_from_meeting["committee_id"]
            ),
            ["id", "name", "forward_to_committee_ids"],
            lock_result=False,
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
                lock_result=False,
            )
            instance["origin_meeting_id"] = origin["meeting_id"]
            instance["all_origin_ids"] = origin.get("all_origin_ids", [])
            instance["all_origin_ids"].append(instance["origin_id"])

    def duplicate_mediafiles(
        self,
        action_data: ActionData,
        forwarded_attachments: dict[int, set[int]],
        meeting_mediafile_replace_map: dict[int, dict[int, int]],
    ) -> tuple[dict[int, set[int]], dict[int, dict[int, int]]]:
        # Extract mediafiles and meeting_mediafiles data
        motion_target_meeting_ids_map: dict[int, set[int]] = (
            self._extract_motion_target_meeting_ids(action_data)
        )
        origin_attachments_data: dict[int, dict[str, Any]] = (
            self._fetch_origin_attachments_data(
                list(motion_target_meeting_ids_map.keys())
            )
        )
        forwarded_attachments, fetched_data = self._prepare_mediafiles_data(
            motion_target_meeting_ids_map,
            origin_attachments_data,
            forwarded_attachments,
        )

        # Calculate new ids and execute dublication actions
        meeting_mediafile_replace_map = self.perform_mediafiles_duplication(
            fetched_data, meeting_mediafile_replace_map
        )
        return forwarded_attachments, meeting_mediafile_replace_map

    def _extract_motion_target_meeting_ids(
        self, action_data: ActionData
    ) -> dict[int, set[int]]:
        """
        Helper method for duplicate_mediafiles.

        Builds mapping: origin_id -> set of meeting_ids
        (only for motions with with_attachments=True).
        """
        motion_target_meeting_ids_map: dict[int, set[int]] = defaultdict(set)
        for instance in action_data:
            if instance.get("with_attachments", False):
                motion_target_meeting_ids_map[instance["origin_id"]].add(
                    instance["meeting_id"]
                )
        return motion_target_meeting_ids_map

    def _fetch_origin_attachments_data(
        self, origin_ids: list[int]
    ) -> dict[int, dict[str, Any]]:
        """Helper method for duplicate_mediafiles."""
        return self.datastore.get_many(
            [
                GetManyRequest(
                    "motion", origin_ids, ["attachment_meeting_mediafile_ids"]
                )
            ],
            lock_result=False,
        )["motion"]

    def _prepare_mediafiles_data(
        self,
        motion_target_meeting_ids_map: dict[int, set[int]],
        origin_attachments_data: dict[int, dict[str, Any]],
        forwarded_attachments: dict[int, set[int]],
    ) -> tuple[dict[int, set[int]], dict[str, dict[int, dict[str, Any]]]]:
        """
        Helper method for duplicate_mediafiles.

        Fetches mediafile and meeting_mediafile data and returns a dictionary of type:
        {
            "mediafile": {id: {instances data}},
            "meeting_mediafile": {id: {data with injected target_meeting_ids}},
        }
        """
        target_meeting_id_mm_ids_map = self._calculate_target_meeting_mm_ids_map(
            motion_target_meeting_ids_map,
            origin_attachments_data,
            forwarded_attachments,
        )
        meeting_mediafile_instances = self._fetch_and_annotate_meeting_mediafiles(
            target_meeting_id_mm_ids_map
        )
        mediafile_instances = self._fetch_mediafiles(
            list(
                {data["mediafile_id"] for data in meeting_mediafile_instances.values()}
            )
        )
        return forwarded_attachments, {
            "mediafile": mediafile_instances,
            "meeting_mediafile": meeting_mediafile_instances,
        }

    def _calculate_target_meeting_mm_ids_map(
        self,
        motion_target_meeting_ids_map: dict[int, set[int]],
        origin_attachments_data: dict[int, dict[str, Any]],
        forwarded_attachments: dict[int, set[int]],
    ) -> dict[int, list[int]]:
        """
        Helper method for _prepare_mediafiles_data.

        Builds a map: target_meeting_id -> list of meeting_mediafile_ids to forward.
        Updates forwarded_attachments to avoid duplication.
        """
        target_map: dict[int, list[int]] = defaultdict(list)
        for origin_id, meeting_ids in motion_target_meeting_ids_map.items():
            attachments = set(
                origin_attachments_data.get(origin_id, {}).get(
                    "attachment_meeting_mediafile_ids", []
                )
            )
            for meeting_id in meeting_ids:
                already_forwarded = forwarded_attachments.get(meeting_id, set())
                new_ids = attachments - already_forwarded
                target_map[meeting_id] = sorted(
                    list(set(target_map[meeting_id]) | new_ids)
                )
                forwarded_attachments[meeting_id].update(attachments)
        return target_map

    def _fetch_and_annotate_meeting_mediafiles(
        self, target_meeting_id_mm_ids_map: dict[int, list[int]]
    ) -> dict[int, dict[str, Any]]:
        """
        Helper method for _prepare_mediafiles_data.

        Fetches meeting_mediafile data and annotates each entry with a list of
        target_meeting_ids where it should be forwarded.
        """
        all_mm_ids = [
            mm_id for ids in target_meeting_id_mm_ids_map.values() for mm_id in ids
        ]
        meeting_mediafiles = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_mediafile",
                    all_mm_ids,
                    [
                        "mediafile_id",
                        "is_public",
                        "access_group_ids",
                        "inherited_access_group_ids",
                        "parent_id",
                    ],
                )
            ],
            lock_result=False,
        )["meeting_mediafile"]

        annotated: dict[int, dict[str, Any]] = defaultdict(dict)
        for meeting_id, mm_ids in target_meeting_id_mm_ids_map.items():
            for mm_id in mm_ids:
                if mm_id in meeting_mediafiles:
                    entry = annotated[mm_id]
                    if not entry:
                        entry.update(meeting_mediafiles[mm_id])
                        entry["target_meeting_ids"] = []
                    entry["target_meeting_ids"].append(meeting_id)
        return annotated

    def _fetch_mediafiles(self, mediafile_ids: list[int]) -> dict[int, dict[str, Any]]:
        """Helper method for _prepare_mediafiles_data"""
        return self.datastore.get_many(
            [
                GetManyRequest(
                    "mediafile",
                    mediafile_ids,
                    ["id", "owner_id", "parent_id", "meeting_mediafile_ids"],
                )
            ],
            lock_result=False,
        )["mediafile"]

    def forward_mediafiles(
        self,
        instance: dict[str, Any],
        meeting_mediafile_replace_map: dict[int, dict[int, int]],
    ) -> dict[str, Any]:
        if replace_map := meeting_mediafile_replace_map.get(instance["meeting_id"], {}):
            attachment_ids = self.datastore.get(
                fqid_from_collection_and_id("motion", instance["origin_id"]),
                ["attachment_meeting_mediafile_ids"],
                lock_result=False,
            ).get("attachment_meeting_mediafile_ids", [])

            instance["attachment_meeting_mediafile_ids"] = [
                mapped_id
                for id_ in attachment_ids
                if (mapped_id := replace_map.get(id_))
            ]
        return instance

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
