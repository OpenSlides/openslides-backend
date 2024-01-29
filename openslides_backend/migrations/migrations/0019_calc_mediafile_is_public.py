from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_and_id_from_fqid


class Migration(BaseEventMigration):
    """
    This migration should check for complete mediafile fields "is_public" and
    "inherited_access_group_ids" and should fill them.
    Strategy:
        1. Build a dict with fqid and data in migrate_event
        2. get_additional_events: Run thru the dict and
           follow the parent_id-chain. Store the highest id of dict
           in each chain in root-list, not it's parent
        3. Go thru the root-list traversing the tree recursively, calculate
           is public and inherited_access_group_ids and generate update requests
           for the 2 fields, when the values differ. Stop the down recursion,
           if the current one isn't changed and the child is not dict of changed mediafiles
        4. Changing group_ids in the inherited_access_group_ids of a mediafile also have
           to be reflected in the group-events

    The algorithm assumes, that the events for a SINGLE mediafile entry are sent in
    correct sequence, because this is guaranteed by the way, the write_requests of
    actions are built.
    Furthermore only the Create-, Update- and ListUpdateEvent are tracked,
    the others do not influence the result
    """

    target_migration_index = 20

    def position_init(self) -> None:
        self.mediafiles: Dict[int, Dict[str, Any]] = defaultdict(dict)
        self.events: List[BaseEvent] = []

    def migrate_event(self, event: BaseEvent) -> Optional[List[BaseEvent]]:
        collection, id_ = collection_and_id_from_fqid(event.fqid)

        if collection != "mediafile":
            return None

        if isinstance(event, CreateEvent):
            self.mediafiles[id_] = event.data
        elif isinstance(event, UpdateEvent):
            if id_ not in self.mediafiles:
                self.mediafiles[id_] = self.new_accessor.get_model_ignore_deleted(
                    event.fqid
                )[0]
            self.mediafiles[id_].update(event.data)
        elif isinstance(event, ListUpdateEvent):
            if id_ not in self.mediafiles:
                self.mediafiles[id_] = self.new_accessor.get_model_ignore_deleted(
                    event.fqid
                )[0]
            if remove_dict := event.remove:
                for key, value in remove_dict.items():
                    if not value:
                        continue
                    old_value = self.mediafiles[id_].get(key)
                    if old_value:
                        self.mediafiles[id_][key] = list(set(old_value) - set(value))
            if add_dict := event.add:
                for key, value in add_dict.items():
                    if not value:
                        continue
                    old_value = self.mediafiles[id_].get(key, set()) or set()
                    self.mediafiles[id_][key] = list(set(old_value) | set(value))
        return None

    def get_additional_events(self) -> Optional[List[BaseEvent]]:
        self.groups: Dict[int, Dict[str, Dict[str, List[int]]]] = defaultdict(dict)
        roots: Set[int] = set()
        for key in self.mediafiles.keys():
            root_id = key
            while (
                parent_id := self.mediafiles[root_id].get("parent_id", 0)
            ) in self.mediafiles.keys():
                root_id = parent_id
            roots.add(root_id)

        for mediafile_id in roots:
            self.check_recursive(mediafile_id)
        for group_id, data in self.groups.items():
            self.events.append(ListUpdateEvent(f"group/{group_id}", data))  # type: ignore
        return self.events

    def check_recursive(self, id_: int) -> None:
        parent_is_public: Optional[bool] = None
        parent_inherited_access_group_ids: Optional[List[int]] = []
        fqid = f"mediafile/{id_}"

        if id_ not in self.mediafiles:
            self.mediafiles[id_] = self.new_accessor.get_model_ignore_deleted(fqid)[0]
        if parent_id := self.mediafiles[id_].get("parent_id"):
            if parent_id not in self.mediafiles:
                self.mediafiles[parent_id] = self.new_accessor.get_model_ignore_deleted(
                    f"mediafile/{parent_id}"
                )[0]
            parent_is_public = cast(bool, self.mediafiles[parent_id].get("is_public"))
            parent_inherited_access_group_ids = cast(
                List, self.mediafiles[parent_id].get("inherited_access_group_ids")
            )
        (
            calc_is_public,
            calc_inherited_access_group_ids,
        ) = calculate_inherited_groups_helper(
            self.mediafiles[id_].get("access_group_ids"),
            parent_is_public,
            parent_inherited_access_group_ids,
        )
        changed: bool = False
        if calc_is_public != self.mediafiles[id_].get(
            "is_public"
        ) or calc_inherited_access_group_ids != self.mediafiles[id_].get(
            "inherited_access_group_ids"
        ):
            changed = True
            add = set(calc_inherited_access_group_ids) - set(
                self.mediafiles[id_].get("inherited_access_group_ids", set())
            )
            if add:
                self.__add_to_group(add, id_, True)
            remove = set(
                self.mediafiles[id_].get("inherited_access_group_ids", set())
            ) - set(calc_inherited_access_group_ids)
            if remove:
                self.__add_to_group(remove, id_, False)
            self.mediafiles[id_]["is_public"] = calc_is_public
            self.mediafiles[id_][
                "inherited_access_group_ids"
            ] = calc_inherited_access_group_ids
            update_event = UpdateEvent(
                fqid,
                {
                    "is_public": calc_is_public,
                    "inherited_access_group_ids": calc_inherited_access_group_ids,
                },
            )
            self.events.append(update_event)

        for child_id in self.mediafiles[id_].get("child_ids", []) or []:
            if changed or child_id in self.mediafiles.keys():
                self.check_recursive(child_id)

    def __add_to_group(self, group_ids: Set[int], mediafile_id: int, add: bool) -> None:
        for group_id in group_ids:
            for group_id in self.groups:
                value_list = set(
                    self.groups[group_id]["add" if add else "remove"][
                        "mediafile_inherited_access_group_ids"
                    ]
                )
                value_list.add(mediafile_id)
                self.groups[group_id]["add" if add else "remove"][
                    "mediafile_inherited_access_group_ids"
                ] = list(value_list)
            else:
                self.groups[group_id] = {
                    "add": {
                        "mediafile_inherited_access_group_ids": (
                            [mediafile_id] if add else []
                        )
                    },
                    "remove": {
                        "mediafile_inherited_access_group_ids": (
                            [] if add else [mediafile_id]
                        )
                    },
                }


def calculate_inherited_groups_helper(
    access_group_ids: Optional[List[int]],
    parent_is_public: Optional[bool],
    parent_inherited_access_group_ids: Optional[List[int]],
) -> Tuple[bool, List[int]]:
    inherited_access_group_ids: List[int]
    is_public = False
    if parent_inherited_access_group_ids and access_group_ids:
        inherited_access_group_ids = [
            id_ for id_ in access_group_ids if id_ in parent_inherited_access_group_ids
        ]
    elif access_group_ids:
        inherited_access_group_ids = access_group_ids
    elif parent_inherited_access_group_ids:
        inherited_access_group_ids = parent_inherited_access_group_ids
    else:
        is_public = parent_is_public is not False
        inherited_access_group_ids = []
    return is_public, inherited_access_group_ids
