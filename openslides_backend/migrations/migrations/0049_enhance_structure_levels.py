from collections import defaultdict
from typing import Any, TypedDict

from openslides_backend.datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)
from openslides_backend.migrations import BaseModelMigration
from openslides_backend.shared.patterns import fqid_from_collection_and_id


class StructureLevelEntry(TypedDict):
    id: int
    meeting_user_ids: list[int]


class Migration(BaseModelMigration):
    target_migration_index = 50

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        next_id = 1
        # map structure level names to ids per meeting
        structure_levels: dict[int, dict[str, StructureLevelEntry]] = defaultdict(dict)
        # map user ids to structure level names and ids.
        default_structure_levels: dict[int, str] = {}
        # remove default_structure_level
        users = self.reader.get_all("user")
        for id, user in users.items():
            if "default_structure_level" in user:
                default_structure_levels[id] = user["default_structure_level"]
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("user", id),
                        {"default_structure_level": None},
                    )
                )

        # migrate structure_level
        meeting_users = self.reader.get_all("meeting_user")
        for id, meeting_user in meeting_users.items():
            meeting_id = meeting_user["meeting_id"]
            user_id = meeting_user["user_id"]
            sl_meeting = structure_levels[meeting_id]
            update: dict[str, Any] = {}
            if name := meeting_user.get("structure_level"):
                update["structure_level"] = None
            elif not (name := default_structure_levels.get(user_id)):
                continue

            if name not in sl_meeting:
                sl_meeting[name] = {"id": next_id, "meeting_user_ids": []}
                next_id += 1
            update["structure_level_ids"] = [sl_meeting[name]["id"]]
            sl_meeting[name]["meeting_user_ids"].append(id)
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("meeting_user", id), update
                )
            )

        # create structure levels
        create_events: list[BaseRequestEvent] = []
        if structure_levels:
            for meeting_id, mapping in structure_levels.items():
                for name, entry in mapping.items():
                    create_events.append(
                        RequestCreateEvent(
                            fqid_from_collection_and_id("structure_level", entry["id"]),
                            {
                                "id": entry["id"],
                                "name": name,
                                "meeting_id": meeting_id,
                                "meeting_user_ids": entry["meeting_user_ids"],
                            },
                        )
                    )
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("meeting", meeting_id),
                        {
                            "structure_level_ids": [
                                entry["id"] for entry in mapping.values()
                            ]
                        },
                    )
                )
        return create_events + events
