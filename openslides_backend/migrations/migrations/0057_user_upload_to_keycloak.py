from datastore.shared.typing import JSON
from datastore.migrations import BaseEventMigration, BaseEvent
from datastore.shared.util import collection_and_id_from_fqid

class Migration(BaseEventMigration):
    """
    This migration adds `group/weight` with the id as the default weight.
    """

    target_migration_index = 58

    collection = "user"
    field = "kc_id"

    def migrate_event(
            self,
            event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, id_ = collection_and_id_from_fqid(event.fqid)

        if collection != "user":
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
