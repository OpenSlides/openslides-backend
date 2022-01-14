from collections import defaultdict

from datastore.migrations import AddFieldMigration, BaseEvent
from datastore.shared.typing import JSON


class SequentialNumberMigration(AddFieldMigration):
    """
    This migration adds `<collection>/sequential_number` with a added up number.
    """

    target_migration_index = None
    collection = None
    field = "sequential_number"

    def __init__(self):
        super().__init__()
        self.sequential_numbers_map = None

    def get_default(self, event: BaseEvent) -> JSON:
        if self.sequential_numbers_map is None:
            self.init_sequential_numbers_map()
        self.sequential_numbers_map[event.data["meeting_id"]] += 1
        return self.sequential_numbers_map[event.data["meeting_id"]]

    def init_sequential_numbers_map(self) -> None:
        ids = self.new_accessor.get_all_ids_for_collection(self.collection)
        self.sequential_numbers_map = defaultdict(int)
        for id_ in ids:
            fqid = self.collection + "/" + str(id_)
            data, _ = self.new_accessor.get_model_ignore_deleted(fqid)
            if self.sequential_numbers_map[data["meeting_id"]] < data.get(
                "sequential_number", 0
            ):
                self.sequential_numbers_map[data["meeting_id"]] = data[
                    "sequential_number"
                ]


class Migration(SequentialNumberMigration):
    """
    This migration adds `motion_comment_section/sequential_number` with a added up number.
    """

    target_migration_index = 20
    collection = "motion_comment_section"
