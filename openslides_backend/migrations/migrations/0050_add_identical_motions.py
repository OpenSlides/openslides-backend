from collections import defaultdict
from typing import NamedTuple

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.datastore.writer.core import (
    BaseRequestEvent,
    RequestUpdateEvent,
)
from openslides_backend.migrations import BaseModelMigration
from openslides_backend.shared.patterns import fqid_from_collection_and_id


class HashKey(NamedTuple):
    meeting_id: int
    lead_motion_id: int | None
    hash: str


class Migration(BaseModelMigration):
    target_migration_index = 51

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        motions = self.reader.get_all("motion")
        hash_map: dict[HashKey, list[int]] = defaultdict(list)
        for id, motion in motions.items():
            if hash := TextHashMixin.get_hash_for_motion(motion):
                key = HashKey(motion["meeting_id"], motion.get("lead_motion_id"), hash)
                hash_map[key].append(id)

        for key, ids in hash_map.items():
            for i, id in enumerate(ids):
                identical_motion_ids = ids[:i] + ids[i + 1 :]
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("motion", id),
                        {
                            "text_hash": key.hash,
                            "identical_motion_ids": identical_motion_ids,
                        },
                    )
                )
        return events
