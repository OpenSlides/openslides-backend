from collections import defaultdict
from typing import Any, cast

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ...models.models import MeetingMediafile
from ...shared.filters import And, FilterOperator, Or
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action
from ..actions.mediafile.duplicate_to_another_meeting import (
    MediafileDuplicateToAnotherMeetingAction,
)
from ..actions.meeting_mediafile.create import MeetingMediafileCreate


class ForwardMediafilesMixin(Action):
    def perform_mediafiles_duplication(
        self,
        fetched_data: dict[str, dict[int, dict[str, Any]]],
        meeting_mediafile_replace_map: dict[int, dict[int, int]] = {},
    ) -> dict[int, dict[int, int]]:
        """
        Duplicates meeting_mediafiles to the meetings defined in target_meeting_ids.
        If related mediafile is meeting-wide also duplicates it.

        Takes dictionary of type:
        {
            "mediafile": {id: {data}},
            "meeting_mediafile": {id: {data}},
        }
        meeting_mediafile data must contain target_meeting_ids for each instance.

        Returns forwarded_attachments, meeting_mediafile_replace_map.
        """
        if not meeting_mediafile_replace_map:
            meeting_mediafile_replace_map = defaultdict(dict)
        (
            mediafiles,
            mediafile_new_mm_map_by_meeting,
            new_mm_instances_data,
            mm_id_target_meeting_ids_map,
        ) = self.map_mediafiles_data(fetched_data)
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
        if new_mm_instances_data:
            meeting_mediafile_replace_map = self._duplicate_meeting_mediafiles(
                new_mm_instances_data,
                mediafile_replace_map_by_meeting,
                meeting_mediafile_replace_map,
            )
        return meeting_mediafile_replace_map

    def map_mediafiles_data(
        self, fetched_data: dict[str, dict[int, dict[str, Any]]]
    ) -> tuple[
        dict[int, dict[str, Any]],
        dict[int, dict[int, dict[str, Any]]],
        list[dict[str, Any]],
        dict[int, set[int]],
    ]:
        """
        Helper method fo perform_mediafiles_duplication.

        Maps the fetched data to:
        1. Dict of related mediafiles.
        2. Map: target_meeting_id -> mediafile_id -> meeting_mediafile data.
        3. Action data for creating new meeting_mediafile instances.
        4. Map: meeting_mediafile_id -> set of target meeting_ids.
        """
        meeting_mediafiles = fetched_data["meeting_mediafile"]
        mediafiles = fetched_data["mediafile"]

        mediafile_new_mm_map_by_meeting: dict[int, dict[int, dict[str, Any]]] = (
            defaultdict(dict)
        )
        new_mm_instances_data: list[dict[str, Any]] = []
        mm_id_target_meeting_ids_map: dict[int, set[int]] = defaultdict(set)

        for mm_id, mm_data in meeting_mediafiles.items():
            new_mm = mm_data.copy()
            target_meeting_ids = new_mm.pop("target_meeting_ids", [])
            for meeting_id in target_meeting_ids:
                mm_instance = {**new_mm, "meeting_id": meeting_id, "old_id": mm_id}
                mediafile_new_mm_map_by_meeting[meeting_id][
                    mm_instance["mediafile_id"]
                ] = mm_instance
                new_mm_instances_data.append(mm_instance)
                mm_id_target_meeting_ids_map[mm_id].add(meeting_id)

        return (
            mediafiles,
            mediafile_new_mm_map_by_meeting,
            new_mm_instances_data,
            mm_id_target_meeting_ids_map,
        )

    def _build_duplication_data_and_mediafile_replace_map(
        self,
        mediafiles: dict,
        mediafile_new_mm_map_by_meeting: dict[int, dict[int, dict[str, Any]]],
        mm_id_target_meeting_map: dict[int, set[int]],
    ) -> tuple[list[dict[str, Any]], dict[int, dict[int, int]]]:
        """
        Helper method fo perform_mediafiles_duplication.

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
        extra_relational_fields_to_meeting = [
            field.own_field_name
            for field in MeetingMediafile().get_fields()
            if field.own_field_name.startswith("used_as_")
        ]

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
                new_mm = {
                    "is_public": entry.get("is_public", False),
                    "mediafile_id": new_mediafile_id,
                    **{
                        field: entry[field]
                        for field in [
                            "meeting_id",
                            "access_group_ids",
                            "inherited_access_group_ids",
                        ]
                        if field in entry
                    },
                    **{
                        field: meeting_id
                        for field in entry
                        if field in extra_relational_fields_to_meeting
                    },
                }
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

    def _get_existing_mm_entries(
        self, instances: list[dict[str, Any]]
    ) -> dict[int, dict[str, Any]]:
        """
        Helper method for _duplicate_meeting_mediafiles.

        Collects existing meeting_mediafile entries that match the given instances
        by their (meeting_id, mediafile_id) combination.
        """
        filter_ = Or(
            And(
                FilterOperator("mediafile_id", "=", entry["mediafile_id"]),
                FilterOperator("meeting_id", "=", entry["meeting_id"]),
            )
            for entry in instances
        )

        return self.datastore.filter(
            "meeting_mediafile",
            filter_,
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
