import json
from collections import defaultdict
from typing import Any, cast

from datastore.migrations import BaseModelMigration
from datastore.shared.services.read_database import HistoryInformation
from datastore.shared.util import collection_from_fqid, fqid_from_collection_and_id
from datastore.writer.core.write_request import (
    BaseRequestEvent,
    ListFieldsData,
    RequestCreateEvent,
    RequestUpdateEvent,
)

from ...shared.history_events import calculate_history_event_payloads


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
                info = position["information"]
                if isinstance(info, str):
                    info = json.loads(info)
                position_nr: int = position["position"]
                models_to_entry_ids = {
                    m_fqid: e_id
                    for e_id, m_fqid in enumerate(
                        sorted(
                            [
                                fqid
                                for fqid in {
                                    *position_to_fqids[position_nr],
                                    *(info if isinstance(info, dict) else {}),
                                }
                                if collection_from_fqid(fqid) in collections
                            ]
                        ),
                        start=next_entry_id,
                    )
                }
                if isinstance(info, list):
                    use_info: dict[str, list[str]] = {
                        mod_fqid: info for mod_fqid in models_to_entry_ids
                    }
                else:
                    use_info = cast(dict[str, list[str]], info)
                create_events, update_events = calculate_history_event_payloads(
                    position.get("user_id"),
                    {
                        fqid: inf
                        for fqid, inf in use_info.items()
                        if collection_from_fqid(fqid) in collections
                    },
                    position_nr,
                    models_to_entry_ids,
                    all_current_fqids,
                    position["timestamp"],
                )
                next_entry_id += len(models_to_entry_ids)
                events.extend(
                    RequestCreateEvent(fqid, fields=cast(dict[str, Any], fields))
                    for fqid, fields in create_events
                )
                events.extend(
                    (
                        RequestUpdateEvent(fqid, fields=cast(dict[str, Any], fields))
                        if "id" in fields
                        else RequestUpdateEvent(
                            fqid, fields={}, list_fields=cast(ListFieldsData, fields)
                        )
                    )
                    for fqid, fields in update_events
                )
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
