from collections import defaultdict
from typing import Any, cast

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
    RestoreEvent,
    UpdateEvent,
)
from datastore.shared.util import collection_and_id_from_fqid, id_from_fqid

cml_permission = "can_manage"  # the only cml-permission
user_cml_permission_field = f"committee_${cml_permission}_management_level"
committee_cml_permission_field = f"user_${cml_permission}_management_level"


class AddRemove:
    def __init__(self) -> None:
        self.add: set[int] = set()
        self.remove: set[int] = set()


class Migration(BaseEventMigration):
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

    More technical:
    In migrate_event there is only the calculation of the changed format of
    field committee_$_management_level made:
    From committee_$1_management_level: ['can_manage'] to committee_$can_manage_management_level: [1]
    The calculation for the opposite relation committee.user_$_management_level,
    the user.committee_ids and the committee.user_ids are made in the
    add_additional_events method, because the event sequence in 1 position isn't guaranteed:
    Maybe the meeting referenced in user.create by group-assigments, still doesn't exist and
    you can't know the committee of this meeting.
    In method get_additional_events the migrated events are applied to the models and you can't
    get the difference between new and old state. To deal with this the user is read before
    the events are applied and calculated after all events of the position are applied.
    """

    target_migration_index = 13

    def position_init(self) -> None:
        self.user_committee_ids: dict[int, AddRemove] = defaultdict(AddRemove)
        self.committee_user_ids: dict[int, AddRemove] = defaultdict(AddRemove)
        self.event_user: list[tuple[BaseEvent, dict[str, Any] | None]] = []

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, user_id = collection_and_id_from_fqid(event.fqid)

        if collection != "user":
            return None

        if isinstance(event, (CreateEvent, UpdateEvent, DeleteEvent, RestoreEvent)):
            user: dict[str, Any] | None
            if not isinstance(event, CreateEvent):
                user = self.new_accessor.get_model_ignore_deleted(f"user/{user_id}")[0]
            else:
                user = None
            if isinstance(event, (CreateEvent, UpdateEvent)):
                cml_committee_ids = list(
                    map(int, event.data.get("committee_$_management_level", []))
                )
                if not cml_committee_ids:
                    self.event_user.append((event, user))
                    return None
                for committee_id in cml_committee_ids:
                    event.data.pop(f"committee_${committee_id}_management_level", None)
                event.data["committee_$_management_level"] = [cml_permission]
                event.data[user_cml_permission_field] = cml_committee_ids
                self.event_user.append((event, user))
                return [event]
            else:
                self.event_user.append((event, user))
        return None

    def get_additional_events(self) -> list[BaseEvent] | None:
        events: list[BaseEvent] = []
        payload: dict[str, dict[str, list[int]]]

        for event, user in self.event_user:
            user_id = id_from_fqid(event.fqid)
            if isinstance(event, CreateEvent):
                add_events = self.handle_user_create_event(event, user_id)
            elif isinstance(event, DeleteEvent):
                add_events = self.handle_user_delete_event(
                    event, cast(dict[str, Any], user), user_id
                )
            elif isinstance(event, RestoreEvent):
                add_events = self.handle_user_restore_event(
                    event, cast(dict[str, Any], user), user_id
                )
            elif isinstance(event, UpdateEvent):
                add_events = self.handle_user_update_event(
                    event, cast(dict[str, Any], user), user_id
                )
            if add_events:
                events.extend(add_events)

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

    def handle_user_create_event(
        self, event: CreateEvent, user_id: int
    ) -> list[BaseEvent] | None:
        meeting_ids = list(map(int, event.data.get("group_$_ids", []))) or []
        committee_ids = cast(
            set[int],
            {
                self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[
                    0
                ].get("committee_id")
                for meeting_id in meeting_ids
            },
        )
        cml_committee_ids = list(
            map(int, event.data.get(user_cml_permission_field, []))
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

        # create the related events for committees
        return [
            ListUpdateEvent(
                f"committee/{committee_id}",
                {
                    "add": {
                        committee_cml_permission_field: [user_id],
                        "user_$_management_level": [cml_permission],
                    }
                },
            )
            for committee_id in cml_committee_ids
        ]

    def handle_user_delete_event(
        self, event: DeleteEvent, user: dict[str, Any], user_id: int
    ) -> list[BaseEvent] | None:
        meeting_ids = list(map(int, cast(list[str], user.get("group_$_ids", [])))) or []
        committee_ids = {
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        }
        cml_committee_ids = cast(list[int], user.get(user_cml_permission_field, []))
        committee_ids.update(cml_committee_ids)
        # don't apply remove on user instance, because it is deleted
        self.update_add_remove(
            self.committee_user_ids,
            cast(list[int], list(committee_ids)),
            [user_id],
            add=False,
        )
        if not cml_committee_ids:
            return None

        # create the related events for committees
        return [
            ListUpdateEvent(
                f"committee/{committee_id}",
                {"remove": {committee_cml_permission_field: [user_id]}},
            )
            for committee_id in cml_committee_ids
        ]

    def handle_user_restore_event(
        self, event: RestoreEvent, user: dict[str, Any], user_id: int
    ) -> list[BaseEvent] | None:
        meeting_ids = list(map(int, cast(list[str], user.get("group_$_ids", [])))) or []
        committee_ids = {
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        }
        cml_committee_ids = cast(list[int], user.get(user_cml_permission_field, []))
        committee_ids.update(cml_committee_ids)
        self.update_add_remove(
            self.committee_user_ids,
            cast(list[int], list(committee_ids)),
            [user_id],
            add=True,
        )
        if not cml_committee_ids:
            return None

        # create the related events for committees
        return [
            ListUpdateEvent(
                f"committee/{committee_id}",
                {"add": {committee_cml_permission_field: [user_id]}},
            )
            for committee_id in cml_committee_ids
        ]

    def handle_user_update_event(
        self, event: UpdateEvent, user: dict[str, Any], user_id: int
    ) -> list[BaseEvent] | None:
        meeting_ids = list(map(int, cast(list[str], user.get("group_$_ids", [])))) or []
        old_committee_ids = {
            self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[0].get(
                "committee_id"
            )
            for meeting_id in meeting_ids
        }
        if "group_$_ids" in event.data:
            meeting_ids = list(map(int, event.data["group_$_ids"]))
            new_committee_ids = {
                self.new_accessor.get_model_ignore_deleted(f"meeting/{meeting_id}")[
                    0
                ].get("committee_id")
                for meeting_id in meeting_ids
            }
        else:
            new_committee_ids = old_committee_ids.copy()

        old_cml_committee_ids = cast(list[int], user.get(user_cml_permission_field, []))
        if user_cml_permission_field in event.data:
            new_cml_committee_ids = list(
                map(int, event.data[user_cml_permission_field])
            )
        else:
            new_cml_committee_ids = old_cml_committee_ids

        new_committee_ids.update(new_cml_committee_ids)
        old_committee_ids.update(old_cml_committee_ids)
        add_committee_ids = cast(list[int], list(new_committee_ids - old_committee_ids))
        remove_committee_ids = cast(
            list[int], list(old_committee_ids - new_committee_ids)
        )
        if add_committee_ids:
            self.update_add_remove(
                self.user_committee_ids,
                [user_id],
                add_committee_ids,
                add=True,
            )
            self.update_add_remove(
                self.committee_user_ids,
                add_committee_ids,
                [user_id],
                add=True,
            )
        if remove_committee_ids:
            self.update_add_remove(
                self.user_committee_ids,
                [user_id],
                remove_committee_ids,
                add=False,
            )
            self.update_add_remove(
                self.committee_user_ids,
                remove_committee_ids,
                [user_id],
                add=False,
            )
        if not new_cml_committee_ids:
            return None

        # create the related events for committees
        add_cml_committee_ids = list(
            set(new_cml_committee_ids) - set(old_cml_committee_ids)
        )
        remove_cml_committee_ids = list(
            set(old_cml_committee_ids) - set(new_cml_committee_ids)
        )
        # create event for committee
        events = [
            ListUpdateEvent(
                f"committee/{committee_id}",
                {
                    "add": {
                        committee_cml_permission_field: [user_id],
                        "user_$_management_level": [cml_permission],
                    }
                },
            )
            for committee_id in add_cml_committee_ids
        ]
        events.extend(
            [
                ListUpdateEvent(
                    f"committee/{committee_id}",
                    {"remove": {committee_cml_permission_field: [user_id]}},
                )
                for committee_id in remove_cml_committee_ids
            ]
        )
        return cast(list[BaseEvent], events)

    def update_add_remove(
        self,
        add_remove_results: dict[int, AddRemove],
        keys: list[int],
        values: list[int],
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
