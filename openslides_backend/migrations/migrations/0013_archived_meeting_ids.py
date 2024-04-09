from typing import Any

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    RestoreEvent,
    UpdateEvent,
)
from openslides_backend.shared.patterns import collection_and_id_from_fqid

ONE_ORGANIZATION_FQID = "organization/1"
ONE_ORGANIZATION_ID = 1


class Migration(BaseEventMigration):
    """
    This migration adds the 1:N relation `organization/archived_meeting_ids` <-> `meeting/is_archived_in_organization_id`.

    Use get_additional_events to add the organization/archived_meeting_ids at
    the end of a position, because organization/1 doesn't need to exist in
    early events of a position. See 0002 for details.
    """

    target_migration_index = 14

    def position_init(self) -> None:
        # Capture all meeting ids to add/remove from
        # `organization/active_meeting_ids` in this position.
        self.meeting_ids_to_add: set[int] = set()
        self.meeting_ids_to_remove: set[int] = set()

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, id_ = collection_and_id_from_fqid(event.fqid)

        if collection != "meeting":
            return None

        if isinstance(event, CreateEvent):
            if event.data.get("is_active_in_organization_id") != ONE_ORGANIZATION_ID:
                event.data["is_archived_in_organization_id"] = ONE_ORGANIZATION_ID
                self.meeting_ids_to_add.add(id_)
                return [event]
        elif isinstance(event, DeleteEvent):
            data, _ = self.new_accessor.get_model_ignore_deleted(event.fqid)
            if data.get("is_active_in_organization_id") != ONE_ORGANIZATION_ID:
                if id_ in self.meeting_ids_to_add:
                    self.meeting_ids_to_add.remove(id_)
                else:
                    self.meeting_ids_to_remove.add(id_)
        elif isinstance(event, RestoreEvent):
            data, _ = self.new_accessor.get_model_ignore_deleted(event.fqid)
            if data.get("is_active_in_organization_id") != ONE_ORGANIZATION_ID:
                if id_ in self.meeting_ids_to_remove:
                    self.meeting_ids_to_remove.remove(id_)
                else:
                    self.meeting_ids_to_add.add(id_)
        elif isinstance(event, DeleteFieldsEvent):
            if "is_active_in_organization_id" in event.data:
                data, _ = self.new_accessor.get_model_ignore_deleted(event.fqid)
                if data.get("is_active_in_organization_id") == ONE_ORGANIZATION_ID:
                    update_event = UpdateEvent(
                        event.fqid,
                        {"is_archived_in_organization_id": ONE_ORGANIZATION_ID},
                    )
                    if id_ in self.meeting_ids_to_remove:
                        self.meeting_ids_to_remove.remove(id_)
                    else:
                        self.meeting_ids_to_add.add(id_)
                    return [event, update_event]
        elif isinstance(event, UpdateEvent):
            if (
                "is_active_in_organization_id" in event.data
                and event.data["is_active_in_organization_id"] == ONE_ORGANIZATION_ID
            ):
                delete_field_event = DeleteFieldsEvent(
                    event.fqid, ["is_archived_in_organization_id"]
                )
                if id_ in self.meeting_ids_to_add:
                    self.meeting_ids_to_add.remove(id_)
                else:
                    self.meeting_ids_to_remove.add(id_)
                return [event, delete_field_event]
            elif (
                "is_active_in_organization_id" in event.data
                and event.data["is_active_in_organization_id"] != ONE_ORGANIZATION_ID
            ):
                event.data["is_archived_in_organization_id"] = ONE_ORGANIZATION_ID
                if id_ in self.meeting_ids_to_remove:
                    self.meeting_ids_to_remove.remove(id_)
                else:
                    self.meeting_ids_to_add.add(id_)
                return [event]
        return None

    def get_additional_events(self) -> list[BaseEvent] | None:
        if not self.meeting_ids_to_add and not self.meeting_ids_to_remove:
            return None

        payload: Any = {}
        if self.meeting_ids_to_add:
            payload["add"] = {"archived_meeting_ids": list(self.meeting_ids_to_add)}
        if self.meeting_ids_to_remove:
            payload["remove"] = {
                "archived_meeting_ids": list(self.meeting_ids_to_remove)
            }

        return [
            ListUpdateEvent(
                ONE_ORGANIZATION_FQID,
                payload,
            )
        ]
