from typing import Any, Dict, List

from ..services.datastore.commands import GetManyRequest
from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import Collection, FullQualifiedId
from .permissions import OrganisationManagementLevel, Permission, permission_parents


def has_perm(
    datastore: DatastoreService, user_id: int, permission: Permission, meeting_id: int
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
    if (
        user.get("organisation_management_level")
        == OrganisationManagementLevel.SUPERADMIN
    ):
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


def is_child_permission(child: Permission, parent: Permission) -> bool:
    """
    Iterate the permission tree (represented in the permissions object) from child to
    parent or until there are no parents anymore
    """
    queue: List[Permission] = [child]
    while queue:
        current = queue.pop()
        if current == parent:
            return True
        parents = permission_parents[current]
        queue.extend(parents)
    return False


def has_organisation_management_level(
    datastore: DatastoreService, user_id: int, set_level: OrganisationManagementLevel
) -> bool:
    """ Checks wether a user has the minimum necessary OrganisationManagementLevel """
    hierarchy: Dict[str, int] = {
        OrganisationManagementLevel.SUPERADMIN: 3,
        OrganisationManagementLevel.CAN_MANAGE_ORGANISATION: 2,
        OrganisationManagementLevel.CAN_MANAGE_USERS: 1,
    }

    if user_id > 0:
        user = datastore.get(
            FullQualifiedId(Collection("user"), user_id),
            ["organisation_management_level"],
        )
        set_level_number = hierarchy.get(set_level, 4)
        actual_level_number = hierarchy.get(
            user.get("organisation_management_level"), 0  # type: ignore
        )
        if actual_level_number >= set_level_number:
            return True
    return False


def is_temporary(datastore: DatastoreService, instance: Dict[str, Any]) -> bool:
    """
    Checks whether the user, identified by the id the instance, is a temporary user.
    Be carefull about the stored meeting id in the instance!
    """
    if "meeting_id" not in instance:
        db_instance = datastore.get(
            FullQualifiedId(Collection("user"), instance["id"]), ["meeting_id"]
        )
        instance["meeting_id"] = db_instance.get("meeting_id")
    return bool(instance.get("meeting_id"))
