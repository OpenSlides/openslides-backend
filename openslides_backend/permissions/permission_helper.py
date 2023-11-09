from typing import List

from openslides_backend.action.mixins.meeting_user_helper import (
    get_groups_from_meeting_user,
)

from ..services.datastore.commands import GetManyRequest
from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import fqid_from_collection_and_id
from .management_levels import CommitteeManagementLevel, OrganizationManagementLevel
from .permissions import Permission, permission_parents


def has_perm(
    datastore: DatastoreService, user_id: int, permission: Permission, meeting_id: int
) -> bool:
    # anonymous cannot be fetched from db
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            [
                "organization_management_level",
            ],
            lock_result=False,
        )
        # superadmins have all permissions
        if (
            user.get("organization_management_level")
            == OrganizationManagementLevel.SUPERADMIN
        ):
            return True

        group_ids = get_groups_from_meeting_user(datastore, meeting_id, user_id)
        if not group_ids:
            return False
    elif user_id == 0:
        # anonymous users are in the default group
        meeting = datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["default_group_id", "enable_anonymous"],
        )
        # check if anonymous is allowed
        if not meeting.get("enable_anonymous"):
            raise PermissionDenied(f"Anonymous is not enabled for meeting {meeting_id}")
        group_ids = [meeting["default_group_id"]]
    else:
        return False

    gmr = GetManyRequest(
        "group",
        group_ids,
        ["permissions", "admin_group_for_meeting_id"],
    )
    result = datastore.get_many([gmr], lock_result=False)
    for group in result["group"].values():
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


def has_organization_management_level(
    datastore: DatastoreService,
    user_id: int,
    expected_level: OrganizationManagementLevel,
) -> bool:
    """Checks wether a user has the minimum necessary OrganizationManagementLevel"""
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["organization_management_level"],
        )
        return expected_level <= OrganizationManagementLevel(
            user.get("organization_management_level")
        )
    return False


def has_committee_management_level(
    datastore: DatastoreService,
    user_id: int,
    expected_level: CommitteeManagementLevel,
    committee_id: int,
) -> bool:
    """Checks wether a user has the minimum necessary CommitteeManagementLevel"""
    if user_id > 0:
        cml_fields = ["committee_management_ids"]
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["organization_management_level", *cml_fields],
            lock_result=False,
            use_changed_models=False,
        )
        if user.get("organization_management_level") in (
            OrganizationManagementLevel.SUPERADMIN,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return True
        if committee_id in user.get("committee_management_ids", []):
            return True
    return False


def filter_surplus_permissions(permission_list: List[Permission]) -> List[Permission]:
    reduced_permissions: List[Permission] = []
    for permission in permission_list:
        if any(
            is_child_permission(permission, possible_parent)
            for possible_parent in permission_list
            if possible_parent != permission
        ):
            continue
        elif permission in reduced_permissions:
            continue
        reduced_permissions.append(permission)
    return reduced_permissions


def is_admin(datastore: DatastoreService, user_id: int, meeting_id: int) -> bool:
    if has_organization_management_level(
        datastore, user_id, OrganizationManagementLevel.SUPERADMIN
    ):
        return True

    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        ["admin_group_id"],
    )
    group_ids = get_groups_from_meeting_user(datastore, meeting_id, user_id)
    return bool(group_ids) and meeting["admin_group_id"] in group_ids
