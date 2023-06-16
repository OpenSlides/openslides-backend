from ...services.datastore.interface import DatastoreService
from ..filters import FilterOperator
from ..util import ONE_ORGANIZATION_FQID


def count_users_for_limit(datastore: DatastoreService) -> int:
    """Counts the users with special conditions to compare with
    limit_of_users."""
    filter_ = FilterOperator("is_active", "=", True)
    active_users = datastore.filter(
        "user",
        filter_,
        [
            "id",
            "organization_management_level",
            "committee_$_management_level",
            "meeting_ids",
        ],
    ).values()
    active_meeting_ids = set(
        datastore.get(ONE_ORGANIZATION_FQID, ["active_meeting_ids"]).get(
            "active_meeting_ids", []
        )
    )
    return len(
        [
            user["id"]
            for user in active_users
            if user.get("organization_management_level")
            or user.get("committee_$_management_level")
            or not (meeting_ids := set(user.get("meeting_ids", set()) or set()))
            or meeting_ids.intersection(active_meeting_ids)
        ]
    )
