import time
from typing import Any

from .interfaces.event import ListFields
from .patterns import fqid_from_collection_and_id
from .typing import FullQualifiedId, HistoryInformation

EventPayload = tuple[FullQualifiedId, dict[str, Any] | ListFields]


def calculate_history_event_payloads(
    user_id: int | None,
    information: HistoryInformation,
    position_id: int,
    model_fqid_to_entry_id: dict[str, int],
    existing_fqids: set[str],
    timestamp: int | None,
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
                "timestamp": timestamp if timestamp is not None else round(time.time()),
                "entry_ids": list(model_fqid_to_entry_id.values()),
                "original_user_id": user_id,
                "user_id": user_id if set_user else None,
            },
        )
    )
    return create_events, update_events
