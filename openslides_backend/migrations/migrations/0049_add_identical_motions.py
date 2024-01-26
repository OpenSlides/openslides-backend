from collections import defaultdict
from typing import Dict, List, NamedTuple, Optional

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.action.actions.motion.mixins import TextHashMixin


class HashKey(NamedTuple):
    meeting_id: int
    lead_motion_id: Optional[int]
    hash: str


class Migration(BaseModelMigration):
    target_migration_index = 50

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        events: List[BaseRequestEvent] = []
        motions = self.reader.get_all("motion")
        hash_map: Dict[HashKey, List[int]] = defaultdict(list)
        for id, motion in motions.items():
            if html := motion.get("text"):
                text = TextHashMixin.get_text_from_html(html)
                hash = TextHashMixin.get_hash(text)
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
