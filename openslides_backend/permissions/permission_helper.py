from typing import Any, Dict, List

from ..services.datastore.commands import GetManyRequest
from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import Collection, FullQualifiedId
from .management_levels import CommitteeManagementLevel, OrganisationManagementLevel
from .permissions import Permission, permission_parents


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
            lock_result=False,
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
        # anonymous users are in the default group
        if user_id == 0:
            meeting = datastore.get(
                FullQualifiedId(Collection("meeting"), meeting_id),
                ["default_group_id", "enable_anonymous"],
            )
            # check if anonymous is allowed
            if not meeting.get("enable_anonymous"):
                raise PermissionDenied(
                    f"Anonymous is not enabled for meeting {meeting_id}"
                )
            group_ids = [meeting["default_group_id"]]
        else:
            return False

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
    datastore: DatastoreService,
    user_id: int,
    expected_level: OrganisationManagementLevel,
) -> bool:
    """ Checks wether a user has the minimum necessary OrganisationManagementLevel """
    if user_id > 0:
        user = datastore.get(
            FullQualifiedId(Collection("user"), user_id),
            ["organisation_management_level"],
        )
        return expected_level <= OrganisationManagementLevel(  # type: ignore
            user.get("organisation_management_level", "no_right")
        )
    return False


def has_committee_management_level(
    datastore: DatastoreService,
    user_id: int,
    expected_level: CommitteeManagementLevel,
    committee_id: int,
) -> bool:
    """ Checks wether a user has the minimum necessary CommitteeManagementLevel """
    if user_id > 0:
        cml_field = f"committee_${committee_id}_management_level"
        user = datastore.get(
            FullQualifiedId(Collection("user"), user_id),
            ["organisation_management_level", cml_field],
        )
        if (
            user.get("organisation_management_level")
            == OrganisationManagementLevel.SUPERADMIN
        ):
            return True
        return expected_level <= CommitteeManagementLevel(  # type: ignore
            user.get(cml_field, "no_right")
        )
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
