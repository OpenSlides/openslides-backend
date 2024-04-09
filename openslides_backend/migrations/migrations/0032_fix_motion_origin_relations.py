from typing import Any

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from openslides_backend.shared.patterns import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)


class Migration(BaseEventMigration):
    target_migration_index = 33

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, id = collection_and_id_from_fqid(event.fqid)
        if collection != "motion":
            return None

        if isinstance(event, CreateEvent):
            if "origin_id" in event.data:
                origin_fqid = fqid_from_collection_and_id(
                    "motion", event.data["origin_id"]
                )
                origin = self.new_accessor.get_model(origin_fqid)
                event.data["origin_meeting_id"] = origin["meeting_id"]
                meeting_fqid = fqid_from_collection_and_id(
                    "meeting", event.data["meeting_id"]
                )
                meeting_update_event = ListUpdateEvent(
                    meeting_fqid, {"add": {"forwarded_motion_ids": [id]}}
                )
                return [event, meeting_update_event]
        elif isinstance(event, DeleteEvent):
            new_events: list[BaseEvent] = [event]
            model: dict[str, Any] = self.new_accessor.get_model(event.fqid)
            if "origin_meeting_id" in model:
                # remove again from reverse meeting field introduced in this migration
                meeting_fqid = fqid_from_collection_and_id(
                    "meeting", model["origin_meeting_id"]
                )
                update_event = ListUpdateEvent(
                    meeting_fqid, {"remove": {"forwarded_motion_ids": [id]}}
                )
                new_events.append(update_event)
            # update all reverse relation fields in other motions
            fields = ["all_origin_ids", "all_derived_motion_ids"]
            for i, field in enumerate(fields):
                for other_motion_id in model.get(field, []):
                    other_motion_fqid = fqid_from_collection_and_id(
                        "motion", other_motion_id
                    )
                    reverse_field_name = fields[1 - i]
                    new_events.append(
                        ListUpdateEvent(
                            other_motion_fqid, {"remove": {reverse_field_name: [id]}}
                        )
                    )
            return new_events
        elif isinstance(event, UpdateEvent):
            """Changes the update event
            Precondition from backend: The backend sorts the events by type: create/update/delete
            Therefore we don't need the self.get_additional_events-method and
            can modify the original event.
            To fix the current migration deleted motions will be removed from the update event
            """
            if "all_derived_motion_ids" in event.data:
                new_derived_motion_ids: list[int] = []
                for motion_id in event.data["all_derived_motion_ids"]:
                    _, deleted = self.new_accessor.get_model_ignore_deleted(
                        fqid_from_collection_and_id("motion", motion_id)
                    )
                    if not deleted:
                        new_derived_motion_ids.append(motion_id)
                event.data["all_derived_motion_ids"] = new_derived_motion_ids
                return [event]
        return None
