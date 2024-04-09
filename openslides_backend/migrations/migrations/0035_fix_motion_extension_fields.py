import re
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
    id_from_fqid,
)

EXTENSION_REFERENCE_IDS_PATTERN = re.compile(r"\[motion[:/](?P<id>\d+)\]")


class Migration(BaseEventMigration):
    """
    Updates `motion/{state|recommendation}_extension` fields to use fqids instead of colons in the
    replacements and fills the `motion/{state|recommendation}_extension_reference_ids` relations
    correctly.
    """

    target_migration_index = 36

    prefixes = ("state", "recommendation")
    list_updates: list[BaseEvent]

    def position_init(self) -> None:
        self.list_updates = []

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection, _ = collection_and_id_from_fqid(event.fqid)
        if collection != "motion":
            return None

        if isinstance(event, CreateEvent):
            self.handle_event("state", event)
        elif isinstance(event, DeleteEvent):
            model: dict[str, Any] = self.new_accessor.get_model(event.fqid)
            for prefix in self.prefixes:
                if f"{prefix}_extension_reference_ids" in model:
                    self.list_updates += [
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
                        if self.will_exist(fqid) and fqid != event.fqid
                    ]
                if f"referenced_in_motion_{prefix}_extension_ids" in model:
                    self.list_updates += [
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
                        if self.will_exist(
                            fqid := fqid_from_collection_and_id("motion", motion_id)
                        )
                        and fqid != event.fqid
                    ]
        elif isinstance(event, UpdateEvent):
            for prefix in self.prefixes:
                self.handle_event(prefix, event)
        return [event]

    def get_additional_events(self) -> list[BaseEvent] | None:
        return self.list_updates

    def handle_event(self, prefix: str, event: CreateEvent | UpdateEvent) -> None:
        if f"{prefix}_extension" in event.data:
            value = event.data[f"{prefix}_extension"]
            replaced_value, motion_fqids = self.extract_and_replace_motion_ids(value)
            # Filter out deleted models
            motion_fqids = [fqid for fqid in motion_fqids if self.will_exist(fqid)]
            event.data[f"{prefix}_extension"] = replaced_value
            event.data[f"{prefix}_extension_reference_ids"] = motion_fqids
            self.list_updates += [
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

    def extract_and_replace_motion_ids(self, value: str) -> tuple[str, list[str]]:
        motion_fqids = []

        def replace(match: Any) -> str:
            motion_id = match.group("id")
            fqid = fqid_from_collection_and_id("motion", motion_id)
            motion_fqids.append(fqid)
            return f"[{fqid}]"

        replaced_value = EXTENSION_REFERENCE_IDS_PATTERN.sub(replace, value)
        return replaced_value, motion_fqids
