from typing import Any, Dict, List, Optional

from datastore.migrations.core.base_migration import BaseMigration
from datastore.migrations.core.events import (
    BaseEvent,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
)
from datastore.shared.util import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)


class Migration(BaseMigration):
    target_migration_index = 33

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection, id = collection_and_id_from_fqid(event.fqid)
        if collection != "motion":
            return None

        if isinstance(event, CreateEvent):
            if "origin_id" in event.data:
                origin = self.new_accessor.get_model(
                    fqid_from_collection_and_id("motion", event.data["origin_id"])
                )
                event.data["origin_meeting_id"] = origin["meeting_id"]
                meeting_fqid = fqid_from_collection_and_id(
                    "meeting", event.data["meeting_id"]
                )
                update_event = ListUpdateEvent(
                    meeting_fqid, {"add": {"forwarded_motion_ids": [id]}}
                )
                return [event, update_event]
        elif isinstance(event, DeleteEvent):
            new_events: List[BaseEvent] = [event]
            model: Dict[str, Any] = self.new_accessor.get_model(event.fqid)
            if "origin_id" in model:
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
        return None
