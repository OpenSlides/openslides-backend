from collections import defaultdict
from typing import Dict, List, Optional, Set, cast

from datastore.migrations import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
    RestoreEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_and_id_from_fqid

cml_permission = "can_manage"  # the only cml-permission


class AddRemove:
    def __init__(self) -> None:
        self.add: Set[int] = set()
        self.remove: Set[int] = set()


class Migration(BaseMigration):
    """
    This migration changes the user.committee_$_management_level-field
    from type TemplateChar to a TemplateRelationListField. The added
    field committee.user_$_management_level is the counter part of the
    newly created relation. Both relations use the new replacement_enum
    instead of a replacement_collection, which must be modified in the
    existing relation, too.
    This migration also fixes the user.committee_ids and commmittee.user_ids
    calculated fields, which may be historic without deletion in older implementation.

    This implemtation assumes, that all changes to the subjects of observation will be
    made directly or indirectly via related relations. Assuming this the migration is
    based only on user events for updates.
    """

    target_migration_index = 13

    def position_init(self) -> None:
        self.user_committee_ids: Dict[int, AddRemove] = defaultdict(AddRemove)
        self.committee_user_ids: Dict[int, AddRemove] = defaultdict(AddRemove)

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection, id = collection_and_id_from_fqid(event.fqid)

        if collection != "user":
            return None

        if isinstance(event, CreateEvent):
            return self.handle_user_create_event(id, event)
        if isinstance(event, DeleteEvent):
            return self.handle_user_delete_event(id, event)
        if isinstance(event, RestoreEvent):
            return self.handle_user_restore_event(id, event)
        elif isinstance(event, UpdateEvent):
            return self.handle_user_update_event(id, event)
        return None

    def handle_user_create_event(
        self, user_id: int, event: CreateEvent
    ) -> Optional[List[BaseEvent]]:
        meeting_ids = list(map(int, event.data.get("group_$_ids", []))) or []
        committee_ids = cast(
            Set[int],
            set(
                self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[
                    0
                ].get("committee_id")
                for meeting_id in meeting_ids
            ),
        )
        cml_committee_ids = list(
            map(int, event.data.get("committee_$_management_level", []))
        )
        committee_ids.update(cml_committee_ids)
        self.update_add_remove(
            self.user_committee_ids, [user_id], list(committee_ids), add=True
        )
        self.update_add_remove(
            self.committee_user_ids, list(committee_ids), [user_id], add=True
        )
        if not cml_committee_ids:
            return None

        # change cml-fields and create event for committee
        for committee_id in cml_committee_ids:
            event.data.pop(f"committee_${committee_id}_management_level")
        event.data["committee_$_management_level"] = [cml_permission]
        event.data[f"committee_${cml_permission}_management_level"] = cml_committee_ids
        return [
            event,
            *[
                ListUpdateEvent(
                    f"committee/{committee_id}",
                    {
                        "add": {
                            f"user_${cml_permission}_management_level": [user_id],
                            "user_$_management_level": [cml_permission],
                        }
                    },
                )
                for committee_id in cml_committee_ids
            ],
        ]

    def handle_user_delete_event(
        self, user_id: int, event: DeleteEvent
    ) -> Optional[List[BaseEvent]]:
        user = self.new_accessor.get_model_ignore_deleted(f"user/{user_id}")[0]
        meeting_ids = list(map(int, cast(List[str], user.get("group_$_ids", [])))) or []
        committee_ids = set(
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        )
        cml_committee_ids = cast(
            List[int], user.get(f"committee_${cml_permission}_management_level", [])
        )
        committee_ids.update(cml_committee_ids)
        # don't apply remove on user instance, because it is deleted
        self.update_add_remove(
            self.committee_user_ids,
            cast(List[int], list(committee_ids)),
            [user_id],
            add=False,
        )
        if not cml_committee_ids:
            return None

        # change create event for committee
        return [
            event,
            *[
                ListUpdateEvent(
                    f"committee/{committee_id}",
                    {"remove": {f"user_${cml_permission}_management_level": [user_id]}},
                )
                for committee_id in cml_committee_ids
            ],
        ]

    def handle_user_restore_event(
        self, user_id: int, event: RestoreEvent
    ) -> Optional[List[BaseEvent]]:
        user = self.new_accessor.get_model_ignore_deleted(f"user/{user_id}")[0]
        meeting_ids = list(map(int, cast(List[str], user.get("group_$_ids", [])))) or []
        committee_ids = set(
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        )
        cml_committee_ids = cast(
            List[int], user.get(f"committee_${cml_permission}_management_level", [])
        )
        committee_ids.update(cml_committee_ids)
        self.update_add_remove(
            self.committee_user_ids,
            cast(List[int], list(committee_ids)),
            [user_id],
            add=True,
        )
        if not cml_committee_ids:
            return None

        # change create event for committee
        events = [
            event,
            *[
                ListUpdateEvent(
                    f"committee/{committee_id}",
                    {"add": {f"user_${cml_permission}_management_level": [user_id]}},
                )
                for committee_id in cml_committee_ids
            ],
        ]
        return events

    def handle_user_update_event(
        self, user_id: int, event: UpdateEvent
    ) -> Optional[List[BaseEvent]]:
        meeting_ids = list(map(int, event.data.get("group_$_ids", []))) or []
        new_committee_ids = set(
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        )
        new_cml_committee_ids = list(
            map(int, event.data.get("committee_$_management_level", []))
        )
        new_committee_ids.update(new_cml_committee_ids)
        user = self.new_accessor.get_model_ignore_deleted(f"user/{user_id}")[0]
        meeting_ids = list(map(int, cast(List[str], user.get("group_$_ids", [])))) or []
        old_committee_ids = set(
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        )
        old_cml_committee_ids = cast(
            List[int], user.get(f"committee_${cml_permission}_management_level", [])
        )
        old_committee_ids.update(old_cml_committee_ids)
        add_committee_ids = new_committee_ids - old_committee_ids
        remove_committee_ids = cast(
            List[int], list(old_committee_ids - new_committee_ids)
        )
        if add_committee_ids:
            self.update_add_remove(
                self.user_committee_ids,
                [user_id],
                cast(List[int], list(add_committee_ids)),
                add=True,
            )
            self.update_add_remove(
                self.committee_user_ids,
                cast(List[int], list(add_committee_ids)),
                [user_id],
                add=True,
            )
        if remove_committee_ids:
            self.update_add_remove(
                self.user_committee_ids,
                [user_id],
                list(remove_committee_ids),
                add=False,
            )
            self.update_add_remove(
                self.committee_user_ids,
                list(remove_committee_ids),
                [user_id],
                add=False,
            )
        if not new_cml_committee_ids:
            return None

        add_cml_committee_ids = list(
            set(new_cml_committee_ids) - set(old_cml_committee_ids)
        )
        remove_cml_committee_ids = list(
            set(old_cml_committee_ids) - set(new_cml_committee_ids)
        )
        # change cml-fields and create event for committee
        for committee_id in new_cml_committee_ids:
            event.data.pop(f"committee_${committee_id}_management_level")
        event.data["committee_$_management_level"] = [cml_permission]
        event.data[
            f"committee_${cml_permission}_management_level"
        ] = new_cml_committee_ids
        events = [
            event,
            *[
                ListUpdateEvent(
                    f"committee/{committee_id}",
                    {
                        "add": {
                            f"user_${cml_permission}_management_level": [user_id],
                            "user_$_management_level": [cml_permission],
                        }
                    },
                )
                for committee_id in add_cml_committee_ids
            ],
            *[
                ListUpdateEvent(
                    f"committee/{committee_id}",
                    {"remove": {f"user_${cml_permission}_management_level": [user_id]}},
                )
                for committee_id in remove_cml_committee_ids
            ],
        ]
        return events

    def update_add_remove(
        self,
        add_remove_results: Dict[int, AddRemove],
        keys: List[int],
        values: List[int],
        add: bool,
    ) -> None:
        if add:
            for key in keys:
                for value in values:
                    if value in add_remove_results[key].remove:
                        add_remove_results[key].remove.remove(value)
                    else:
                        add_remove_results[key].add.add(value)
        else:
            for key in keys:
                for value in values:
                    if value in add_remove_results[key].add:
                        add_remove_results[key].add.remove(value)
                    else:
                        add_remove_results[key].remove.add(value)

    def get_additional_events(self) -> Optional[List[BaseEvent]]:
        events: Optional[List[BaseEvent]] = []
        payload: Dict[str, Dict[str, List[int]]]
        for user_id, committee_ids in self.user_committee_ids.items():
            payload = {}
            if committee_ids.add:
                payload["add"] = {"committee_ids": list(committee_ids.add)}
            if committee_ids.remove:
                payload["remove"] = {"committee_ids": list(committee_ids.remove)}
            events.append(ListUpdateEvent(f"user/{user_id}", payload))  # type: ignore

        for committee_id, user_ids in self.committee_user_ids.items():
            payload = {}
            if user_ids.add:
                payload["add"] = {"user_ids": list(user_ids.add)}
            if user_ids.remove:
                payload["remove"] = {"user_ids": list(user_ids.remove)}
            events.append(ListUpdateEvent(f"committee/{committee_id}", payload))  # type: ignore

        return events
