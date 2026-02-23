from typing import Any

from openslides_backend.services.database.interface import Database

from ...shared.filters import And, Filter, FilterOperator


def get_meeting_user_filter(meeting_id: int, user_id: int) -> Filter:
    return And(
        FilterOperator("meeting_id", "=", meeting_id),
        FilterOperator("user_id", "=", user_id),
    )


def get_meeting_user(
    datastore: Database, meeting_id: int, user_id: int, fields: list[str]
) -> dict[str, Any] | None:
    result = datastore.filter(
        "meeting_user",
        get_meeting_user_filter(meeting_id, user_id),
        fields,
        lock_result=False,
    )
    if result:
        return next(iter(result.values()))
    return None


def get_groups_from_meeting_user(
    datastore: Database, meeting_id: int, user_id: int
) -> list[int]:
    meeting_user = get_meeting_user(datastore, meeting_id, user_id, ["group_ids"])
    if not meeting_user:
        return []
    return meeting_user.get("group_ids") or []
