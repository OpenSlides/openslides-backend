from os import environ
from ...services.datastore.interface import DatastoreService
from ..filters import FilterOperator
from ..util import ONE_ORGANIZATION_FQID
from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import ActionException


def count_users_for_limit(datastore: DatastoreService) -> int:
    """Counts the users with special conditions to compare with
    limit_of_users."""
    env = Environment(environ)
    if (count_mode := env.get_user_count_mode()) not in ["standard", "no_archived_meetings"]:
        raise ActionException(f"{count_mode} is no valid USER_COUNT_MODE. See readme in backend repo for environment variables!")

    filter_ = FilterOperator("is_active", "=", True)
    if count_mode == "standard":
        return datastore.count("user", filter_, lock_result=False)

    active_users = datastore.filter(
        "user",
        filter_,
        [
            "id",
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
            if (meeting_ids := set(user.get("meeting_ids", set())))
            and meeting_ids.intersection(active_meeting_ids)
        ]
    )
