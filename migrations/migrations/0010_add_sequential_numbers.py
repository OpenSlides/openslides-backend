from collections import defaultdict
from typing import List, Optional

from datastore.migrations import BaseEvent, BaseMigration, CreateEvent
from datastore.shared.typing import JSON
from datastore.shared.util import KEYSEPARATOR, collection_from_fqid


class Migration(BaseMigration):
    """
    This migration adds `<collection>/sequential_number` with a added up number.
    """

    target_migration_index = 11

    collections = (
        "assignment",
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

    def __init__(self):
        super().__init__()
        self.sequential_numbers_map = None

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection in self.collections and isinstance(event, CreateEvent):
            event.data[self.field] = self.get_default(event, collection)
            return [event]
        else:
            return None

    def get_default(self, event: BaseEvent, collection: str) -> JSON:
        if self.sequential_numbers_map is None:
            self.init_sequential_numbers_map()
        self.sequential_numbers_map[collection][event.data["meeting_id"]] += 1
        return self.sequential_numbers_map[collection][event.data["meeting_id"]]

    def init_sequential_numbers_map(self) -> None:
        self.sequential_numbers_map = {}
        for collection in self.collections:
            self.sequential_numbers_map[collection] = defaultdict(int)
            ids = self.new_accessor.get_all_ids_for_collection(collection)
            for id_ in ids:
                fqid = collection + KEYSEPARATOR + str(id_)
                data, _ = self.new_accessor.get_model_ignore_deleted(fqid)
                if self.sequential_numbers_map[collection][
                    data["meeting_id"]
                ] < data.get("sequential_number", 0):
                    self.sequential_numbers_map[collection][data["meeting_id"]] = data[
                        "sequential_number"
                    ]
