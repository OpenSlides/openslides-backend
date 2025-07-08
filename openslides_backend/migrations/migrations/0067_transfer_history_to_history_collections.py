import json
from collections import defaultdict
from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.shared.services.read_database import HistoryInformation
from datastore.shared.util import collection_from_fqid, fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)


class Migration(BaseModelMigration):
    """
    This migration transcribes the entire history into the history collections
    """

    target_migration_index = 68
    chunk_length = 1000

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        collections = ["motion", "assignment", "user"]
        all_current_fqids: set[str] = set()
        for collection in collections:
            all_current_fqids.update(
                fqid_from_collection_and_id(collection, id_)
                for id_ in self.reader.get_all(collection, ["id"])
            )
        max_position = self.reader.get_max_position()
        cur_max_pos = 0
        next_entry_id = 1
        events: list[BaseRequestEvent] = []
        user_fqid_to_position_ids: dict[str, list[int]] = defaultdict(list)
        model_fqid_to_entry_ids: dict[str, list[int]] = defaultdict(list)
        while cur_max_pos <= max_position:
            cur_min_pos = cur_max_pos
            cur_max_pos += self.chunk_length
            history_chunk: list[HistoryInformation]
            position_to_fqids: dict[int, list[str]]
            history_chunk, position_to_fqids = self.reader.get_history_positions(
                cur_min_pos, cur_max_pos
            )
            for position in history_chunk:
                start_entry_id = next_entry_id
                info = position["information"]
                if isinstance(info, str):
                    info = json.loads(info)
                position_nr: int = position["position"]
                if isinstance(info, list):
                    for fqid in position_to_fqids.get(position_nr, []):
                        if collection_from_fqid(fqid) in collections:
                            do_relation = fqid in all_current_fqids
                            events.append(
                                RequestCreateEvent(
                                    fqid_from_collection_and_id(
                                        "history_entry", next_entry_id
                                    ),
                                    {
                                        "id": next_entry_id,
                                        "entries": info,
                                        "original_model_id": fqid,
                                        "model_id": fqid if do_relation else None,
                                        "position_id": position_nr,
                                    },
                                )
                            )
                            if do_relation:
                                model_fqid_to_entry_ids[fqid].append(next_entry_id)
                            next_entry_id += 1
                else:
                    assert isinstance(info, dict)
                    for fqid, information in info.items():
                        if collection_from_fqid(fqid) in collections:
                            do_relation = fqid in all_current_fqids
                            events.append(
                                RequestCreateEvent(
                                    fqid_from_collection_and_id(
                                        "history_entry", next_entry_id
                                    ),
                                    {
                                        "id": next_entry_id,
                                        "entries": information,
                                        "original_model_id": fqid,
                                        "model_id": fqid if do_relation else None,
                                        "position_id": position_nr,
                                    },
                                )
                            )
                            if do_relation:
                                model_fqid_to_entry_ids[fqid].append(next_entry_id)
                            next_entry_id += 1
                do_relation = (
                    fqid_from_collection_and_id("user", position["user_id"])
                    in all_current_fqids
                )
                events.append(
                    RequestCreateEvent(
                        fqid_from_collection_and_id("history_position", position_nr),
                        {
                            "id": position_nr,
                            "timestamp": position["timestamp"],
                            "original_user_id": position["user_id"],
                            "user_id": position["user_id"] if do_relation else None,
                            "entry_ids": list(range(start_entry_id, next_entry_id)),
                        },
                    )
                )
                if do_relation:
                    user_fqid_to_position_ids[
                        fqid_from_collection_and_id("user", position["user_id"])
                    ].append(position_nr)
        all_update_fqids: set[str] = {
            *model_fqid_to_entry_ids,
            *user_fqid_to_position_ids,
        }
        for fqid in all_update_fqids:
            payload: dict[str, Any] = {}
            if posit_ids := user_fqid_to_position_ids.get(fqid):
                payload["history_position_ids"] = posit_ids
            if entry_ids := model_fqid_to_entry_ids.get(fqid):
                payload["history_entry_ids"] = entry_ids
            events.append(RequestUpdateEvent(fqid, payload))
        return events
