import re
from typing import Any, Dict, List, Optional, Tuple, Union

from datastore.migrations.core.base_migration import BaseMigration
from datastore.migrations.core.events import (
    BaseEvent,
    CreateEvent,
    DeleteEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from datastore.shared.util import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)

from openslides_backend.shared.patterns import id_from_fqid

EXTENSION_REFERENCE_IDS_PATTERN = re.compile(r"\[motion[:/](?P<id>\d+)\]")


class Migration(BaseMigration):
    """
    Updates `motion/{state|recommendation}_extension` fields to use fqids instead of colons in the
    replacements and fills the `motion/{state|recommendation}_extension_reference_ids` relations
    correctly.
    """

    target_migration_index = 35

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection, id = collection_and_id_from_fqid(event.fqid)
        if collection != "motion":
            return None

        if isinstance(event, CreateEvent):
            return [event, *self.handle_event("state", event)]
        elif isinstance(event, DeleteEvent):
            model: Dict[str, Any] = self.new_accessor.get_model(event.fqid)
            new_events: List[BaseEvent] = [event]
            for prefix in ("recommendation", "state"):
                if f"{prefix}_extension_reference_ids" in model:
                    new_events += [
                        ListUpdateEvent(
                            fqid,
                            {
                                "remove": {
                                    f"referenced_in_motion_{prefix}_extension_ids": [
                                        id_from_fqid(event.fqid)
                                    ]
                                }
                            },
                        )
                        for fqid in model[f"{prefix}_extension_reference_ids"]
                        if self.new_accessor.get_model_ignore_deleted(fqid)[1] is False
                    ]
                if f"referenced_in_motion_{prefix}_extension_ids" in model:
                    new_events += [
                        ListUpdateEvent(
                            fqid,
                            {
                                "remove": {
                                    f"{prefix}_extension_reference_ids": [event.fqid]
                                }
                            },
                        )
                        for motion_id in model[
                            f"referenced_in_motion_{prefix}_extension_ids"
                        ]
                        if self.new_accessor.get_model_ignore_deleted(
                            (fqid := fqid_from_collection_and_id("motion", motion_id))
                        )[1]
                        is False
                    ]
            return new_events
        elif isinstance(event, UpdateEvent):
            return [
                event,
                *self.handle_event("recommendation", event),
                *self.handle_event("state", event),
            ]
        return None

    def handle_event(
        self, prefix: str, event: Union[CreateEvent, UpdateEvent]
    ) -> List[BaseEvent]:
        if f"{prefix}_extension" in event.data:
            value = event.data[f"{prefix}_extension"]
            replaced_value, motion_fqids = self.extract_and_replace_motion_ids(value)
            # Filter out deleted models
            motion_fqids = [
                fqid
                for fqid in motion_fqids
                if self.new_accessor.model_exists(fqid)
                and self.new_accessor.get_model_ignore_deleted(fqid)[1] is False
            ]
            event.data[f"{prefix}_extension"] = replaced_value
            event.data[f"{prefix}_extension_reference_ids"] = motion_fqids
            return [
                ListUpdateEvent(
                    fqid,
                    {
                        "add": {
                            f"referenced_in_motion_{prefix}_extension_ids": [
                                id_from_fqid(event.fqid)
                            ]
                        }
                    },
                )
                for fqid in motion_fqids
            ]
        return []

    def extract_and_replace_motion_ids(self, value: str) -> Tuple[str, List[str]]:
        motion_fqids = []

        def replace(match: Any) -> str:
            motion_id = match.group("id")
            fqid = fqid_from_collection_and_id("motion", motion_id)
            motion_fqids.append(fqid)
            return f"[{fqid}]"

        replaced_value = EXTENSION_REFERENCE_IDS_PATTERN.sub(replace, value)
        return replaced_value, motion_fqids
