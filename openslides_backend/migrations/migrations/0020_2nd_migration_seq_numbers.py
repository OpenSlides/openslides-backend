from collections import defaultdict
from typing import cast

from datastore.migrations import BaseEvent, BaseEventMigration, CreateEvent
from datastore.shared.typing import JSON
from datastore.shared.util import KEYSEPARATOR, collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration renumbers all `<collection>/sequential_number` to get them unique.
    """

    target_migration_index = 21

    collections = (
        "assignment",
        "motion",
        "motion_block",
        "motion_category",
        "motion_workflow",
        "poll",
        "projector",
        "topic",
        "list_of_speakers",
        "motion_statute_paragraph",
        "motion_comment_section",
    )
    field = "sequential_number"

    def __init__(self) -> None:
        super().__init__()
        self.sequential_numbers_map: dict[str, dict[int, int]] = {}

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        if collection in self.collections and isinstance(event, CreateEvent):
            event.data[self.field] = self.get_default(event, collection)
            return [event]
        else:
            return None

    def get_default(self, event: BaseEvent, collection: str) -> JSON:
        if not self.sequential_numbers_map:
            self.init_sequential_numbers_map()
        self.sequential_numbers_map[collection][
            cast(int, event.data["meeting_id"])
        ] += 1
        return self.sequential_numbers_map[collection][
            cast(int, event.data["meeting_id"])
        ]

    def init_sequential_numbers_map(self) -> None:
        self.sequential_numbers_map = {}
        for collection in self.collections:
            self.sequential_numbers_map[collection] = defaultdict(int)
            ids = self.new_accessor.get_all_ids_for_collection(collection)
            for id_ in ids:
                fqid = collection + KEYSEPARATOR + str(id_)
                data, _ = self.new_accessor.get_model_ignore_deleted(fqid)
                if self.sequential_numbers_map[collection][
                    cast(int, data["meeting_id"])
                ] < cast(int, data.get("sequential_number", 0)):
                    self.sequential_numbers_map[collection][
                        cast(int, data["meeting_id"])
                    ] = cast(int, data["sequential_number"])
