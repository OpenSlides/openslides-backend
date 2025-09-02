from collections import defaultdict
from datetime import datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

from .interfaces.event import ListFields
from .patterns import FullQualifiedId, fqid_from_collection_and_id, id_from_fqid
from .typing import HistoryInformation

EventPayload = tuple[FullQualifiedId, dict[str, Any] | ListFields]


def calculate_history_event_payloads(
    user_id: int | None,
    information: HistoryInformation,
    position_id: int,
    model_fqid_to_entry_id: dict[str, int],
    model_fqid_to_meeting_id: dict[str, int | None],
    existing_fqids: set[str],
    timestamp: int | None = None,
) -> tuple[list[EventPayload], list[EventPayload]]:
    transformed_information = [
        (model_fqid_to_entry_id[fqid], fqid, entries)
        for fqid, entries in information.items()
    ]
    create_events: list[EventPayload] = [
        (
            fqid_from_collection_and_id("history_entry", id_),
            {
                "id": id_,
                "entries": entries,
                "position_id": position_id,
                "original_model_id": fqid,
                "model_id": (fqid if fqid in existing_fqids else None),
                "meeting_id": model_fqid_to_meeting_id.get(fqid, None),
            },
        )
        for id_, fqid, entries in transformed_information
    ]
    update_events: list[EventPayload] = [
        (
            fqid,
            {"add": {"history_entry_ids": [id_]}},
        )
        for id_, fqid, entries in transformed_information
        if fqid in existing_fqids
    ]
    meeting_to_entry_ids: dict[int, list[int]] = defaultdict(list)
    for entry in create_events:
        if meeting_id := cast(dict[str, Any], entry[1]).get("meeting_id"):
            meeting_to_entry_ids[meeting_id].append(id_from_fqid(entry[0]))
    update_events.extend(
        [
            (
                fqid_from_collection_and_id("meeting", meeting_id),
                {"add": {"relevant_history_entry_ids": ids}},
            )
            for meeting_id, ids in meeting_to_entry_ids.items()
        ]
    )
    if set_user := (
        user_id
        and user_id > 0
        and fqid_from_collection_and_id("user", user_id) in existing_fqids
    ):
        update_events.append(
            (
                fqid_from_collection_and_id("user", user_id),
                {"add": {"history_position_ids": [position_id]}},
            )
        )
    create_events.append(
        (
            fqid_from_collection_and_id("history_position", position_id),
            {
                "id": position_id,
                "timestamp": (
                    timestamp
                    if timestamp is not None
                    else datetime.now(ZoneInfo("UTC"))
                ),
                "entry_ids": list(model_fqid_to_entry_id.values()),
                "original_user_id": user_id,
                "user_id": user_id if set_user else None,
            },
        )
    )
    return create_events, update_events
