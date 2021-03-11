from typing import List

from ..services.datastore.commands import GetManyRequest
from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import Collection, FullQualifiedId
from .permissions import permissions


def has_perm(
    datastore: DatastoreService, user_id: int, permission: str, meeting_id: int
) -> bool:
    # anonymous cannot be fetched from db
    if user_id > 0:
        user = datastore.get(
            FullQualifiedId(Collection("user"), user_id),
            [
                f"group_${meeting_id}_ids",
                "guest_meeting_ids",
                "organisation_management_level",
            ],
        )
    else:
        user = {}

    # superadmins have all permissions
    if user.get("organisation_management_level") == "superadmin":
        return True

    # get correct group ids for this user
    if user.get(f"group_${meeting_id}_ids"):
        group_ids = user[f"group_${meeting_id}_ids"]
    else:
        # guests, temporary users and anonymous are in the default group
        if meeting_id in user.get("guest_meeting_ids", []) or user_id == 0:
            meeting = datastore.get(
                FullQualifiedId(Collection("meeting"), meeting_id),
                ["default_group_id", "enable_anonymous"],
            )
            # check if anonymous is allowed
            if user_id == 0 and not meeting.get("enable_anonymous"):
                raise PermissionDenied(
                    f"Anonymous is not enabled for meeting {meeting_id}"
                )
            group_ids = [meeting["default_group_id"]]
        else:
            raise PermissionDenied(f"You do not belong to meeting {meeting_id}")

    gmr = GetManyRequest(
        Collection("group"),
        group_ids,
        ["permissions", "admin_group_for_meeting_id"],
    )
    result = datastore.get_many([gmr])
    for group in result[Collection("group")].values():
        # admins implicitly have all permissions
        if group.get("admin_group_for_meeting_id") == meeting_id:
            return True
        # check if the current group has the needed permission (or a higher one)
        for group_permission in group.get("permissions", []):
            if is_child_permission(permission, group_permission):
                return True
    return False


def is_child_permission(child: str, parent: str) -> bool:
    """
    Iterate the permission tree (represented in the permissions object) from child to
    parent or until there are no parents anymore
    """
    queue: List[str] = [child]
    while queue:
        current = queue.pop()
        if current == parent:
            return True
        parents = permissions[current]
        queue.extend(parents)
    return False
