from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.reader.core import GetManyRequestPart
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core.write_request import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)

from ...shared.filters import And, FilterOperator, Not, Or
from ...shared.patterns import collection_and_id_from_fqid


class Migration(BaseModelMigration):
    """
    This migration removes mistakenly created history collection entries
    """

    target_migration_index = 71
    chunk_length = 1000

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        if self.reader.is_in_memory_migration:
            return None
        collections = ["motion", "assignment", "user"]
        events: list[BaseRequestEvent] = []
        filter_ = And(
            Not(
                Or(
                    FilterOperator("original_model_id", "%=", f"{collection}/%")
                    for collection in collections
                )
            ),
            FilterOperator("meta_deleted", "!=", True),
        )
        broken_entries = self.reader.filter(
            "history_entry", filter_, ["position_id", "model_id", "meeting_id"]
        )
        if broken_entries:
            collection_to_broken_ids: dict[str, list[int]] = defaultdict(list)
            broken_position_ids: set[int] = set()
            meeting_to_broken_entry_ids: dict[int, list[str | int]] = {}
            entry_model_fqids: set[str] = set()
            for entry in broken_entries.values():
                broken_position_ids.add(entry["position_id"])
                if meeting_id := entry.get("meeting_id"):
                    meeting_to_broken_entry_ids[meeting_id] = []
                if model_id := entry.get("model_id"):
                    collection, id_ = collection_and_id_from_fqid(model_id)
                    collection_to_broken_ids[collection].append(id_)
                    entry_model_fqids.add(model_id)
            all_broken_models = self.reader.get_many(
                [
                    GetManyRequestPart(collection, ids, ["id"])
                    for collection, ids in collection_to_broken_ids.items()
                ]
            )
            for collection, ids in collection_to_broken_ids.items():
                entry_model_fqids.difference_update(
                    {
                        f"{collection}/{id_}"
                        for id_ in ids
                        if id_ not in all_broken_models.get(collection, {})
                    }
                )
            all_broken_positions = self.reader.get_many(
                [
                    GetManyRequestPart(
                        "history_position",
                        list(broken_position_ids),
                        ["user_id", "entry_ids"],
                    )
                ]
            ).get("history_position", {})
            deletable_position_ids = {
                pos_id
                for pos_id, position in all_broken_positions.items()
                if not any(
                    [
                        entry_id not in broken_entries
                        for entry_id in position["entry_ids"]
                    ]
                )
            }
            broken_position_to_broken_entry_ids: dict[int, list[str | int]] = {
                pos_id: []
                for pos_id in all_broken_positions
                if pos_id not in deletable_position_ids
            }
            for id_, entry in broken_entries.items():
                if meeting_id := entry.get("meeting_id"):
                    meeting_to_broken_entry_ids[meeting_id].append(id_)
                    if (
                        pos_id := entry["position_id"]
                    ) in broken_position_to_broken_entry_ids:
                        broken_position_to_broken_entry_ids[pos_id].append(id_)
            user_to_deletable_position_ids: dict[int, list[str | int]] = {
                user_id: []
                for pos_id in deletable_position_ids
                if (user_id := all_broken_positions[pos_id].get("user_id"))
            }
            for pos_id in deletable_position_ids:
                if user_id := all_broken_positions[pos_id].get("user_id"):
                    user_to_deletable_position_ids[user_id].append(pos_id)
            events = [
                *[
                    RequestUpdateEvent(fqid, fields={"history_entry_ids": None})
                    for fqid in entry_model_fqids
                ],
                *[
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("user", user_id),
                        fields={},
                        list_fields={"remove": {"history_position_ids": pos_ids}},
                    )
                    for user_id, pos_ids in user_to_deletable_position_ids.items()
                ],
                *[
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("meeting", meeting_id),
                        fields={},
                        list_fields={
                            "remove": {"relevant_history_entry_ids": entry_ids}
                        },
                    )
                    for meeting_id, entry_ids in meeting_to_broken_entry_ids.items()
                ],
                *[
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("history_position", pos_id),
                        fields={},
                        list_fields={"remove": {"entry_ids": entry_ids}},
                    )
                    for pos_id, entry_ids in broken_position_to_broken_entry_ids.items()
                ],
                *[
                    RequestDeleteEvent(
                        fqid_from_collection_and_id("history_position", pos_id)
                    )
                    for pos_id in deletable_position_ids
                ],
                *[
                    RequestDeleteEvent(
                        fqid_from_collection_and_id("history_entry", entry_id)
                    )
                    for entry_id in broken_entries
                ],
            ]

        return events
