import time
from collections import defaultdict
from typing import Any, cast

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.shared.typing import HistoryInformation
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.filters import And, FilterOperator, Or
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...util.typing import ActionData, ActionResultElement, ActionResults
from ..mediafile.duplicate_to_another_meeting import (
    MediafileDuplicateToAnotherMeetingAction,
)
from ..meeting_mediafile.create import MeetingMediafileCreate
from ..motion_change_recommendation.create import MotionChangeRecommendationCreateAction
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
        motion_target_meeting_ids_map: dict[int, set[int]] = (
            self._extract_motion_target_meeting_ids(action_data)
        )
        origin_attachments_data: dict[int, dict[str, Any]] = (
            self._fetch_origin_attachments_data(
                list(motion_target_meeting_ids_map.keys())
            )
        )
        mm_id_target_meeting_ids_map, forwarded_attachments = (
            self._build_target_meeting_and_mm_maps(
                motion_target_meeting_ids_map,
                origin_attachments_data,
                forwarded_attachments,
            )
        )
        mediafiles, mediafile_new_mm_map_by_meeting, new_mm_instances_data = (
            self._fetch_and_map_mediafiles(mm_id_target_meeting_ids_map)
        )
        duplicate_mediafiles_data, mediafile_replace_map_by_meeting = (
            self._build_duplication_data_and_mediafile_replace_map(
                mediafiles,
                mediafile_new_mm_map_by_meeting,
                mm_id_target_meeting_ids_map,
            )
        )
        if duplicate_mediafiles_data:
            self.execute_other_action(
                MediafileDuplicateToAnotherMeetingAction, duplicate_mediafiles_data
            )
        meeting_mediafile_replace_map = self._duplicate_meeting_mediafiles(
            new_mm_instances_data,
            mediafile_replace_map_by_meeting,
            meeting_mediafile_replace_map,
        )
        return forwarded_attachments, meeting_mediafile_replace_map

    def _extract_motion_target_meeting_ids(
        self, action_data: ActionData
    ) -> dict[int, set[int]]:
        """
        Builds mapping: origin_id -> set of meeting_ids (only for motions with attachments).
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
        return self.datastore.get_many(
            [
                GetManyRequest(
                    "motion", origin_ids, ["attachment_meeting_mediafile_ids"]
                )
            ],
            lock_result=False,
        )["motion"]

    def _build_target_meeting_and_mm_maps(
        self,
        motion_target_meeting_ids_map: dict[int, set[int]],
        origin_attachments_data: dict[int, dict[str, Any]],
        forwarded_attachments: dict[int, set[int]],
    ) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
        """
        Build a map: meeting_mediafile_id -> set of target meeting_ids.
        Updates map: forwarded_attachments: target_meeting_id -> set of
        origin attachments to forward.

        Skips attachments already forwarded when processing
        other amendments within the same tranaction.
        """
        target_meeting_id_mm_ids_map: dict[int, list[int]] = defaultdict(list)
        for origin_id, meeting_ids in motion_target_meeting_ids_map.items():
            origin_motion_data = origin_attachments_data.get(origin_id, {})
            attachments = set(
                origin_motion_data.get("attachment_meeting_mediafile_ids", [])
            )
            for meeting_id in meeting_ids:
                forwarded_mediafiles_ids = forwarded_attachments.get(meeting_id, set())
                target_meeting_id_mm_ids_map[meeting_id] = sorted(
                    list(
                        set(target_meeting_id_mm_ids_map[meeting_id])
                        | attachments - forwarded_mediafiles_ids
                    )
                )
                forwarded_attachments[meeting_id].update(attachments)
        mm_id_target_meeting_ids_map: dict[int, set[int]] = defaultdict(set)
        for meeting_id, attachment_ids in target_meeting_id_mm_ids_map.items():
            for mm_id in attachment_ids:
                mm_id_target_meeting_ids_map[mm_id].add(meeting_id)
        return mm_id_target_meeting_ids_map, forwarded_attachments

    def _fetch_and_map_mediafiles(
        self, mm_id_target_meeting_ids_map: dict[int, set[int]]
    ) -> tuple[
        dict[int, dict[str, Any]],
        dict[int, dict[int, dict[str, Any]]],
        list[dict[str, Any]],
    ]:
        """
        Retrieves data based on the data from mm_id_target_meeting_ids_map:
        1. Dict of related mediafiles.
        2. Map:target_meeting_ids -> forwarded mediafile id -> target meeting_mediafile data
        3. List with target meeting_mediafile data.
        """
        meeting_mediafiles = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_mediafile",
                    list(mm_id_target_meeting_ids_map.keys()),
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

        mediafile_new_mm_map_by_meeting: dict[int, dict[int, dict[str, Any]]] = (
            defaultdict(dict)
        )
        new_mm_instances_data: list[dict[str, Any]] = []
        for mm_id, mm_data in meeting_mediafiles.items():
            for meeting_id in mm_id_target_meeting_ids_map[mm_id]:
                mm = {**mm_data, "meeting_id": meeting_id, "old_id": mm_id}
                mediafile_new_mm_map_by_meeting[meeting_id][mm["mediafile_id"]] = mm
                new_mm_instances_data.append(mm)

        mediafile_ids = {
            meeting_mediafile["mediafile_id"]
            for meeting_mediafile in meeting_mediafiles.values()
        }
        mediafiles = self.datastore.get_many(
            [
                GetManyRequest(
                    "mediafile",
                    list(mediafile_ids),
                    ["id", "owner_id", "parent_id", "meeting_mediafile_ids"],
                )
            ],
            lock_result=False,
        )["mediafile"]

        return mediafiles, mediafile_new_mm_map_by_meeting, new_mm_instances_data

    def _build_duplication_data_and_mediafile_replace_map(
        self,
        mediafiles: dict,
        mediafile_new_mm_map_by_meeting: dict[int, dict[int, dict[str, Any]]],
        mm_id_target_meeting_map: dict[int, set[int]],
    ) -> tuple[list[dict[str, Any]], dict[int, dict[int, int]]]:
        """
        Builds:
        - action_data for MediafileDuplicateToAnotherMeetingAction
        - Map: meeting_id -> origin mediafile id -> target_mediafile_id
        """
        if meeting_wide_mediafiles := {
            mediafile_id: mediafile
            for mediafile_id, mediafile in mediafiles.items()
            if mediafile["owner_id"] != ONE_ORGANIZATION_FQID
        }:
            new_mediafiles_ids = iter(
                self.datastore.reserve_ids(
                    "mediafile",
                    sum(
                        len(mm_id_target_meeting_map.get(id_, []))
                        for mediafile in meeting_wide_mediafiles.values()
                        for id_ in mediafile.get("meeting_mediafile_ids", [])
                    ),
                )
            )

        duplicate_mediafiles_data: list[dict[str, Any]] = []
        mediafile_replace_map_by_meeting: dict[int, dict[int, int]] = {}
        for meeting_id, mm_map in mediafile_new_mm_map_by_meeting.items():
            replace_map = mediafile_replace_map_by_meeting.setdefault(meeting_id, {})
            for origin_mediafile_id in mm_map.keys():
                if origin_mediafile_id in meeting_wide_mediafiles:
                    replace_map[origin_mediafile_id] = next(new_mediafiles_ids)
                else:
                    replace_map[origin_mediafile_id] = origin_mediafile_id

            meeting_fqid = fqid_from_collection_and_id("meeting", meeting_id)
            for origin_id, target_id in replace_map.items():
                if origin_id != target_id:
                    new_mediafile = {
                        "id": target_id,
                        "owner_id": meeting_fqid,
                        "origin_id": origin_id,
                    }
                    if parent_id := mediafiles.get(origin_id, {}).get("parent_id"):
                        new_mediafile["parent_id"] = replace_map.get(parent_id)
                    duplicate_mediafiles_data.append(new_mediafile)
        return duplicate_mediafiles_data, mediafile_replace_map_by_meeting

    def _get_existing_mm_entries(
        self, instances: list[dict[str, Any]]
    ) -> dict[int, dict[str, Any]]:
        """
        Helper method for _duplicate_meeting_mediafiles.
        Collects existing meeting_mediafile entries that match the given instances
        by their (meeting_id, mediafile_id) combination.
        """
        filters = [
            And(
                FilterOperator("mediafile_id", "=", entry["mediafile_id"]),
                FilterOperator("meeting_id", "=", entry["meeting_id"]),
            )
            for entry in instances
        ]
        if not filters:
            return {}

        return self.datastore.filter(
            "meeting_mediafile",
            Or(*filters),
            ["id", "mediafile_id", "meeting_id"],
            lock_result=False,
            use_changed_models=False,
        )

    def _update_mm_replace_map(
        self,
        origin_data: list[dict[str, Any]],
        forwarded_data: list[dict[str, Any]],
        mediafile_replace_map_by_meeting: dict[int, dict[int, int]],
        meeting_mediafile_replace_map: dict[int, dict[int, int]],
        existing_mm_imstances: dict[tuple[int, int], int],
    ) -> None:
        """
        Helper method for _duplicate_meeting_mediafiles.
        Updates meeting_mediafile_replace_map with newly created instances where
        no prior match existed in the target (meeting_id, mediafile_id).
        """
        for origin, forwarded in zip(origin_data, forwarded_data):
            meeting_id = origin["meeting_id"]
            new_mediafile_id = mediafile_replace_map_by_meeting[meeting_id][
                origin["mediafile_id"]
            ]
            key = (meeting_id, new_mediafile_id)

            if key not in existing_mm_imstances:
                meeting_mediafile_replace_map[meeting_id].update(
                    {origin["old_id"]: forwarded["id"]}
                )

    def _duplicate_meeting_mediafiles(
        self,
        new_mm_instances_data: list[dict[str, Any]],
        mediafile_replace_map_by_meeting: dict[int, dict[int, int]],
        meeting_mediafile_replace_map: dict[int, dict[int, int]],
    ) -> dict[int, dict[int, int]]:
        """
        Duplicates meeting_mediafiles and updates the replacement map for assigning them
        to motions, avoiding duplicates based on (meeting_id, mediafile_id) combinations.
        """
        retrieved_instances = self._get_existing_mm_entries(new_mm_instances_data)
        existing_mm_imstances = {
            (entry["meeting_id"], entry["mediafile_id"]): entry["id"]
            for entry in retrieved_instances.values()
        }

        new_mm_action_data = []
        for entry in new_mm_instances_data:
            meeting_id = entry["meeting_id"]
            old_mediafile_id = entry["mediafile_id"]
            new_mediafile_id = mediafile_replace_map_by_meeting[meeting_id][
                old_mediafile_id
            ]
            key = (meeting_id, new_mediafile_id)

            if key in existing_mm_imstances:
                meeting_mediafile_replace_map[meeting_id].update(
                    {entry["old_id"]: existing_mm_imstances[key]}
                )
            else:
                new_mm = {**entry}
                new_mm.pop("old_id")
                new_mm["mediafile_id"] = new_mediafile_id
                new_mm_action_data.append(new_mm)

        created_results = cast(
            list[dict[str, Any]],
            self.execute_other_action(MeetingMediafileCreate, new_mm_action_data),
        )

        self._update_mm_replace_map(
            new_mm_instances_data,
            created_results,
            mediafile_replace_map_by_meeting,
            meeting_mediafile_replace_map,
            existing_mm_imstances,
        )

        return meeting_mediafile_replace_map

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
