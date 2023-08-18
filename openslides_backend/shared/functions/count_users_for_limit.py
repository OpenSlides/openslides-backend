from os import environ
from typing import List, Optional, Sequence, Tuple, Union

from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import ActionException

from ...services.datastore.interface import DatastoreService
from ..filters import FilterOperator
from ..util import ONE_ORGANIZATION_FQID

UserEstimationParam = Sequence[
    Union[Tuple[bool, Sequence[int]], Sequence[int]]
]  # Tuple of user.is_active, user.meeting_ids or list of user.id


def count_users_for_limit(datastore: DatastoreService) -> int:
    """Counts the users with special conditions to compare with
    limit_of_users."""
    count_mode = get_validated_user_count_mode()
    filter_ = FilterOperator("is_active", "=", True)
    if count_mode == "standard":
        return datastore.count(
            "user", filter_, lock_result=False, use_changed_models=False
        )

    active_users = datastore.filter(
        "user",
        filter_,
        [
            "id",
            "meeting_ids",
        ],
        lock_result=False,
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
            if (meeting_ids := user.get("meeting_ids"))
            and any(
                meeting_id
                for meeting_id in meeting_ids
                if meeting_id in active_meeting_ids
            )
        ]
    )


def get_user_counting_to_add_function(
    old: UserEstimationParam, new: Optional[UserEstimationParam] = None
) -> int:
    # def case_create() -> int:
    #    if is_active and user_meeting_ids

    # if old and not new and type(old) == tuple:
    return 0


def is_user_counted(
    user_id: int,
    user_is_active: Optional[bool] = None,
    user_meeting_ids: Optional[List[int]] = None,
    active_meeting_ids: Optional[List[int]] = None,
    datastore: Optional[DatastoreService] = None,
) -> bool:
    """Response to question 'Is this user counted in the respective user_count_mode'.
    If you have you could give all needed parameters to get the response or you give
    a database instance and let the function read all it needs from db
    """
    necessary_user_fields = []
    user_count_mode = get_validated_user_count_mode()
    if type(user_is_active) != bool:
        necessary_user_fields.append("user_is_active")

    if user_count_mode != "standard":
        if type(user_meeting_ids) != list or any(
            type(v) != int for v in user_meeting_ids
        ):
            necessary_user_fields.append("user_meeting_ids")
        if type(user_meeting_ids) != list or any(
            type(v) != int for v in user_meeting_ids
        ):
            necessary_user_fields.append("user_meeting_ids")

        # , active_meeting_ids])
    if not isinstance(datastore, DatastoreService) and any(
        f is None for f in necessary_user_fields
    ):
        raise ActionException("Missing information, datastore as parameter needed!")
    # read all parameters with None value

    # user_fields = [for f in [user_is_active, user_meeting_ids] if f is None]
    # check all parameters beeing correct
    if user_count_mode == "standard":
        return user_is_active
    else:
        return user_is_active and any(
            meeting_id
            for meeting_id in user_meeting_ids
            if meeting_id in active_meeting_ids
        )


def get_validated_user_count_mode() -> str:
    env = Environment(environ)
    if (count_mode := env.get_user_count_mode()) not in [
        "standard",
        "no_archived_meetings",
    ]:
        raise ActionException(
            f"{count_mode} is no valid USER_COUNT_MODE. See readme in backend repo for environment variables!"
        )
    return count_mode
