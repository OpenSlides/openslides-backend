from typing import List, Optional

from ...services.datastore.interface import DatastoreService
from ..filters import FilterOperator
from ..util import ONE_ORGANIZATION_FQID, fqid_from_collection_and_id


def count_users_for_limit(datastore: DatastoreService) -> int:
    """Counts the users with special conditions to compare with
    limit_of_users."""
    filter_ = FilterOperator("is_active", "=", True)
    active_users = datastore.filter(
        "user", filter_, ["group_ids", "organization_management_level", "committee_ids"]
    ).values()
    count = 0
    for user in active_users:
        if user.get("organization_management_level"):
            count += 1
        elif user.get("committee_ids"):
            count += 1
        elif check_meeting(datastore, user.get("group_ids")):
            count += 1
    return count


def check_meeting(datastore: DatastoreService, group_ids: Optional[List[int]]) -> bool:
    if not group_ids:
        return True
    organization = datastore.get(ONE_ORGANIZATION_FQID, ["archived_meeting_ids"])
    for group_id in group_ids:
        group = datastore.get(
            fqid_from_collection_and_id("group", group_id), ["meeting_id"]
        )
        if group["meeting_id"] not in organization["archived_meeting_ids"]:
            return True
    return False
