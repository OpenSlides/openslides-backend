from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from .interfaces.event import ListFields
from .patterns import FullQualifiedId, fqid_from_collection_and_id
from .typing import HistoryInformation, HistoryInformationData

EventPayload = tuple[FullQualifiedId, dict[str, Any] | ListFields]


def build_history_information_data(
    entries: list[str] | None = None,
    structured_information: dict[str, Any] | None = None,
) -> HistoryInformationData:
    data: HistoryInformationData = {}
    if entries is not None:
        data["entries"] = entries
    if structured_information is not None:
        data["structured_information"] = structured_information
    return data


def update_history_information(
    information: HistoryInformation,
    fqid: FullQualifiedId,
    entries: list[str] | None = None,
    structured_information: dict[str, Any] | None = None,
) -> None:
    """Updates history information for fqid"""
    if fqid not in information:
        information[fqid] = build_history_information_data(
            entries, structured_information
        )
    else:
        if entries:
            information[fqid].setdefault("entries", list()).extend(entries)
        if structured_information:
            information[fqid].setdefault("structured_information", dict()).update(
                structured_information
            )


def update_history_information_multi(
    information: HistoryInformation,
    fqids: list[FullQualifiedId],
    entries: list[str] | None = None,
    structured_information: dict[str, Any] | None = None,
) -> None:
    """
    Adds given HistoryInformation to the given information for every fqid in fqids.
    """
    for fqid in fqids:
        update_history_information(information, fqid, entries, structured_information)


def calculate_history_event_payloads(
    user_id: int | None,
    information: HistoryInformation,
    position_id: int,
    model_fqid_to_entry_id: dict[str, int],
    model_fqid_to_meeting_id: dict[str, int | None],
    existing_fqids: set[str],
    timestamp: int | None = None,
) -> list[EventPayload]:
    transformed_information = [
        (
            model_fqid_to_entry_id[fqid],
            fqid,
            data.get("entries") or None,
            data.get("structured_information"),
        )
        for fqid, data in information.items()
    ]
    create_events: list[EventPayload] = [
        (
            fqid_from_collection_and_id("history_entry", id_),
            {
                "id": id_,
                "entries": entries,
                "structured_information": (
                    Jsonb(structured_information) if structured_information else None
                ),
                "position_id": position_id,
                "original_model_id": fqid,
                "model_id": (fqid if fqid in existing_fqids else None),
                "meeting_id": model_fqid_to_meeting_id.get(fqid, None),
            },
        )
        for id_, fqid, entries, structured_information in transformed_information
    ]
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
                "original_user_id": user_id,
                "user_id": (
                    user_id
                    if (
                        user_id
                        and user_id > 0
                        and fqid_from_collection_and_id("user", user_id)
                        in existing_fqids
                    )
                    else None
                ),
            },
        )
    )
    return create_events
